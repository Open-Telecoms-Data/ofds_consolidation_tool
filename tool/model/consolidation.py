from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, Iterable, List, Set, Tuple, Type

import uuid
import json
import logging

from qgis.core import QgsVectorLayer, QgsProject, QgsFeature

from .network import Node, Network, Span, FeatureT
from .comparison import (
    NodeComparison,
    NodeComparisonOutcome,
    ConsolidationReason,
    SpanComparison,
    ComparisonT,
    SpanComparisonOutcome,
)

logger = logging.getLogger(__name__)


# TODO: sort by diagonal distance
class AbstractNetworkConsolidator(Generic[FeatureT, ComparisonT], ABC):

    FeatureCls: Type[FeatureT]

    PROPS_TO_COPY: List[str]

    # TODO: deduplicate array values
    PROPS_TO_MERGE_ARRAYS: List[str]
    PROPS_TO_SUM: List[str]

    # TODO: if identical, don't concat
    PROPS_TO_CONCAT: List[str]

    network_b_ids_map: Dict[str, str]

    @abstractmethod
    def get_comparisons_to_ask_user(self) -> List[ComparisonT]: ...

    def _merge_features(self, primary: FeatureT, secondary: FeatureT) -> FeatureT:
        # Update ID map to keep track of which IDs have been reassigned
        self.network_b_ids_map[secondary.id] = primary.id

        # TODO: Add provenance to properties, perhaps combine with existing info

        # Merge properties
        props = self._merge_features_properties(primary, secondary)

        # Create merged Feature
        return self.FeatureCls(
            primary.id, props, primary.featureId, primary.featureGeometry
        )

    def _merge_features_properties(
        self, primary: FeatureT, secondary: FeatureT
    ) -> Dict[str, Any]:
        props = primary.properties.copy()

        def set_prop(k, v):
            # Support nested propes too via slash notation
            if "/" in k:
                k_parts = k.split("/")
                props[k_parts[0]] = props.get(k_parts[0]) or {}
                props[k_parts[0]][k_parts[1]] = v
            else:
                props[k] = v

        # Copy over properties that exist in B but not A
        for k in self.PROPS_TO_COPY:
            if primary.get(k) is None:
                if secondary.get(k) is not None:
                    set_prop(k, secondary.get(k))

        # Merge array properties
        for k in self.PROPS_TO_MERGE_ARRAYS:
            if primary.get(k) is not None or secondary.get(k) is not None:
                prop_a = primary.get(k) or list()
                prop_b = secondary.get(k) or list()
                set_prop(k, list(prop_a) + list(prop_b))

        # Sum properties
        for k in self.PROPS_TO_SUM:
            if primary.get(k) is not None and secondary.get(k) is not None:
                set_prop(k, (primary.get(k) or 0) + (secondary.get(k) or 0))

        # Concat (with a comma) string properties
        for k in self.PROPS_TO_CONCAT:
            if primary.get(k) is not None and secondary.get(k) is not None:
                strs = [feat.get(k) for feat in [primary, secondary] if feat.get(k)]
                set_prop(k, ", ".join(strs))

        return props


class NetworkNodesConsolidator(AbstractNetworkConsolidator[Node, NodeComparison]):
    """
    Builder class to get the comparisons out of a pair of networks.
    """

    FeatureCls = Node

    network_a: Network
    network_b: Network

    merge_threshold: int
    ask_threshold: int
    match_radius_km: float

    user_comparisons: List[NodeComparison]
    outcomes: List[NodeComparisonOutcome]

    # Lookup for Id's of nodes from Network B after consolidation
    network_b_ids_map: Dict[str, str]

    # When consolidating nodes, these properties should be copied from secondary to
    # primary if they don't exist on the primary.
    PROPS_TO_COPY = [
        "name",
        "location",
        "address",
        "type",
        "accessPoint",
        "power",
        "physicalInfrastructureProvider",
    ]

    # When consolidating nodes, these properties are arrays that should be concatenated.
    PROPS_TO_MERGE_ARRAYS = [
        "type",
        "internationalConnections",
        "technologies",
        "networkProviders",
    ]

    # TODO: Figure out which properties to sum/concat in Nodes
    PROPS_TO_SUM = []
    PROPS_TO_CONCAT = []

    def __init__(
        self,
        network_a: Network,
        network_b: Network,
        merge_above: int = 100,
        ask_above: int = 0,
        match_radius_km: float = 10.0,
    ):
        self.network_a = network_a
        self.network_b = network_b
        self.merge_threshold = merge_above
        self.ask_threshold = ask_above
        self.match_radius_km = match_radius_km
        self.outcomes = list()
        self.user_comparisons = []
        self.network_b_ids_map = dict()

        self._compare_nodes()

    def _compare_nodes(self):
        """
        Create NodeComparisons, and check for either auto-merging or give to the UI to
        ask the user.
        """
        for a_node in self.network_a.nodes:
            for b_node in self.network_b.nodes:
                comparison = NodeComparison(a_node, b_node)
                if comparison.distance_km > self.match_radius_km:
                    # No chance of match, just add immedate no-consolidate outcome
                    self.add_comparison_outcomes(
                        [
                            NodeComparisonOutcome(
                                comparison=comparison, consolidate=False
                            )
                        ]
                    )

                elif comparison.confidence > self.merge_threshold:
                    # Auto-consolidate
                    matching_properties = comparison.get_high_scoring_properties()
                    reason = ConsolidationReason(
                        feature_type="NODE",
                        primary=comparison.node_a,
                        secondary=comparison.node_b,
                        confidence=comparison.confidence,
                        matching_properties=matching_properties,
                        manual=False,
                    )
                    outcome = NodeComparisonOutcome(
                        comparison=comparison, consolidate=reason
                    )
                    self.add_comparison_outcomes([outcome])

                elif comparison.confidence >= self.ask_threshold:
                    #   todo: get user pref for which network to keep
                    #   todo: ability to merge rather than replace? (stretch goal)
                    self.user_comparisons.append(comparison)

    def get_comparisons_to_ask_user(self) -> List[NodeComparison]:
        return self.user_comparisons

    def add_comparison_outcomes(
        self,
        outcomes: Iterable[NodeComparisonOutcome],
    ):
        self.outcomes.extend(outcomes)

    def _gather_nodes_from_outcomes(self, outcomes: List[NodeComparisonOutcome]):
        """
        This method implements the results of a comparison i.e. consolidating (or not)
        and creates the consolidated network's Nodes.
        """

        # Index of all nodes
        nodes_a = {o.comparison.node_a.id: o.comparison.node_a for o in outcomes}
        nodes_b = {o.comparison.node_b.id: o.comparison.node_b for o in outcomes}

        # Index which nodes from A and B have been consolidated
        consolidated_ids_a: Set[str] = set(
            o.comparison.node_a.id
            for o in outcomes
            if isinstance(o.consolidate, ConsolidationReason)
        )
        consolidated_ids_b: Set[str] = set(
            o.comparison.node_b.id
            for o in outcomes
            if isinstance(o.consolidate, ConsolidationReason)
        )

        # Index which nodes from A and B aren't consolidated, and can be directly output
        unconsolidated_ids_a: Set[str] = set(nodes_a.keys()).difference(
            consolidated_ids_a
        )
        unconsolidated_ids_b: Set[str] = set(nodes_b.keys()).difference(
            consolidated_ids_b
        )

        # Output nodes
        nodes: Dict[str, Node]
        nodes = dict()

        # Create + Gather consolidated nodes
        for outcome in outcomes:
            if isinstance(outcome.consolidate, ConsolidationReason):
                assert isinstance(outcome.consolidate.primary, Node)
                assert isinstance(outcome.consolidate.secondary, Node)
                consolidated_node = self._merge_features(
                    outcome.consolidate.primary,
                    outcome.consolidate.secondary,
                )
                logger.info(f"Creating consolidated node: {consolidated_node.name}")
                assert consolidated_node.id not in nodes
                nodes[consolidated_node.id] = consolidated_node

        # Gather unconsolidated nodes from A
        for _id in unconsolidated_ids_a:
            assert _id not in nodes
            nodes[_id] = nodes_a[_id]

        # Gather unconsolidated nodes from B, creating new IDs if there's a clash
        for _id in unconsolidated_ids_b:
            if _id in nodes:
                # rewrite ID of node B
                logger.info("Found Node in Network B with an existing ID, rewriting.")
                new_node = nodes_b[_id].with_new_id(str(uuid.uuid4()))
                assert new_node.id not in nodes
                nodes[new_node.id] = new_node
            else:
                assert _id not in nodes
                nodes[_id] = nodes_b[_id]

        return set(nodes.values())

    def _remap_network_b_span_node_ids(self, span: Span) -> Span:
        new_properties = span.properties.copy()
        p_start = new_properties["start"]
        p_end = new_properties["end"]

        # Check in case properties have been loaded as nested JSON string
        if isinstance(p_start, str):
            p_start = json.loads(p_start)

        if isinstance(p_end, str):
            p_end = json.loads(p_end)

        if p_start["id"] in self.network_b_ids_map:
            p_start["id"] = self.network_b_ids_map[p_start["id"]]

        if p_end["id"] in self.network_b_ids_map:
            p_end["id"] = self.network_b_ids_map[p_end["id"]]

        new_properties["start"] = p_start
        new_properties["end"] = p_end

        new_span = Span(
            span.id,
            properties=new_properties,
            featureId=span.featureId,
            featureGeometry=span.featureGeometry,
        )
        return new_span

    def get_networks_with_consolidated_nodes(self) -> Tuple[Network, Network]:
        nodes = list(self._gather_nodes_from_outcomes(self.outcomes))
        qgs_layer, nodes = self._qgis_layer_from_nodes(nodes)

        # Network A IDs never change, so no remapping needed
        new_network_a = Network(
            nodes=nodes,
            nodesLayer=qgs_layer,
            spans=self.network_a.spans,
            spansLayer=self.network_a.spansLayer,
        )

        # Network B span start/end IDs may be remapped
        new_network_b = Network(
            nodes=nodes,
            nodesLayer=qgs_layer,
            spans=list(
                self._remap_network_b_span_node_ids(span)
                for span in self.network_b.spans
            ),
            spansLayer=self.network_b.spansLayer,
        )

        return (new_network_a, new_network_b)

    def _qgis_layer_from_nodes(
        self, nodes: List[Node]
    ) -> Tuple[QgsVectorLayer, List[Node]]:
        LAYER_NAME = "_ofds_consolidated_nodes"

        project = QgsProject.instance()
        assert project

        # Remove an old intermediate layers from previous tool uses
        if len(project.mapLayersByName(LAYER_NAME)) > 0:
            project.removeMapLayers(
                [layer.id() for layer in project.mapLayersByName(LAYER_NAME)]
            )

        # Create the new QgsVectorLayer from consolidated Nodes
        # TODO: Tidy up (i.e. remove) this layer after we're done?
        layer_uri = "Point?crs=epsg:4326&index=yes"
        layer = QgsVectorLayer(layer_uri, LAYER_NAME, "memory")
        layer.setCustomProperty("skipMemoryLayersCheck", 1)

        layer_data = layer.dataProvider()
        assert layer_data  # type: ignore

        fields = Node.get_qgs_fields()

        layer.startEditing()
        layer_data.addAttributes(fields.toList())
        layer.commitChanges()

        logger.debug(f"Adding {len(nodes)} Nodes to QgsVectorLayer")

        new_nodes: List[Node] = list()

        # Create a new QgsFeature for each new Node, copying old Geometry
        #  + consolidated properties
        #  + new Nodes because featureId changes w/ a new layer
        for node in nodes:
            new_feature = QgsFeature(fields)
            new_feature.setGeometry(node.featureGeometry)
            for field in fields:
                if field.name() in node.properties:
                    new_feature.setAttribute(
                        field.name(), node.properties[field.name()]
                    )
            layer_data.addFeature(new_feature)
            new_nodes.append(
                Node(node.id, node.properties, new_feature.id(), new_feature.geometry())
            )

        layer.updateExtents()

        # TODO: Change visibility from True to False when we're not testing anymore
        #       or make it a setting?
        project.addMapLayer(layer, True)

        return (layer, new_nodes)


class NetworkSpansConsolidator(AbstractNetworkConsolidator[Span, SpanComparison]):

    FeatureCls = Span

    network_a: Network
    network_b: Network

    matched_spans_in_a: Set[str]
    matched_spans_in_b: Set[str]

    network_b_ids_map: Dict[str, str]

    comparison_outcomes: List[NodeComparisonOutcome]

    PROPS_TO_COPY = [
        "name",
        "phase",
        "status",
        "readyForServiceDate",
        "physicalInfrastructureProvider",
        "supplier",
        "deploymentDetails",
        "darkFibre",
        "fibreType",
        "fibreTypeDetails/fibreSubType",
        "fibreCount",
        "capacityDetails",
    ]

    PROPS_TO_MERGE_ARRAYS = [
        "transmissionMedium",
        "deployment",
        "countries",
    ]

    PROPS_TO_SUM = [
        "capacity",
    ]

    PROPS_TO_CONCAT = [
        "deploymentDetails/description",
        "capacityDetails/description",
        "fibreTypeDetails/description",
    ]

    def __init__(self, network_a: Network, network_b: Network):
        self.network_a = network_a
        self.network_b = network_b
        self.network_b_ids_map = dict()
        self.matched_spans_in_a = set()
        self.matched_spans_in_b = set()
        self.comparison_outcomes = list()

    def get_comparisons_to_ask_user(self) -> List[SpanComparison]:
        network_a_index: Dict[Tuple[str, str], Span]
        network_a_index = dict()

        # Build index of lookups from (start, end) to Span for Network A
        for span_a in self.network_a.spans:
            network_a_index[(span_a.start_id, span_a.end_id)] = span_a

        matches: List[SpanComparison]
        matches = list()

        # Check Spans in Network B against Network A via the index
        for span_b in self.network_b.spans:
            # See if this span matches one in Network A
            span_a_lookup = network_a_index.get((span_b.start_id, span_b.end_id))

            # If not, check reverse end/start
            if span_a_lookup is None:
                span_a_lookup = network_a_index.get((span_b.end_id, span_b.start_id))

            # Got a match!
            if span_a_lookup is not None:
                matches.append(SpanComparison(span_a_lookup, span_b))
                self.matched_spans_in_a.add(span_a_lookup.id)
                self.matched_spans_in_b.add(span_b.id)

        return matches

    def _gather_spans_from_outcomes(self, outcomes: List[SpanComparisonOutcome]):
        """
        This method implements the results of a comparison i.e. consolidating (or not)
        and creates the consolidated network's Spans.
        """

        # Index of all spans
        spans_a = {s.id: s for s in self.network_a.spans}
        spans_b = {s.id: s for s in self.network_b.spans}

        # Index which nodes from A and B have been consolidated
        consolidated_ids_a: Set[str] = set(
            o.comparison.span_a.id
            for o in outcomes
            if isinstance(o.consolidate, ConsolidationReason)
        )
        consolidated_ids_b: Set[str] = set(
            o.comparison.span_b.id
            for o in outcomes
            if isinstance(o.consolidate, ConsolidationReason)
        )

        # Index which nodes from A and B aren't consolidated, and can be directly output
        unconsolidated_ids_a: Set[str] = set(spans_a.keys()).difference(
            consolidated_ids_a
        )

        unconsolidated_ids_b: Set[str] = set(spans_b.keys()).difference(
            consolidated_ids_b
        )

        # Output spans
        spans: Dict[str, Span]
        spans = dict()

        # Create + Gather consolidated spans
        for outcome in outcomes:
            if isinstance(outcome.consolidate, ConsolidationReason):
                assert isinstance(outcome.consolidate.primary, Span)
                assert isinstance(outcome.consolidate.secondary, Span)
                consolidated_span = self._merge_features(
                    outcome.consolidate.primary,
                    outcome.consolidate.secondary,
                )
                logger.info(f"Creating consolidated node: {consolidated_span.name}")
                assert consolidated_span.id not in spans
                spans[consolidated_span.id] = consolidated_span

        # Gather unconsolidated nodes from A
        for _id in unconsolidated_ids_a:
            assert _id not in spans
            spans[_id] = spans_a[_id]

        # Gather unconsolidated nodes from B, creating new IDs if there's a clash
        for _id in unconsolidated_ids_b:
            if _id in spans:
                # rewrite ID of node B
                logger.info("Found Span in Network B with an existing ID, rewriting.")
                new_node = spans_b[_id].with_new_id(str(uuid.uuid4()))
                assert new_node.id not in spans
                spans[new_node.id] = new_node
            else:
                assert _id not in spans
                spans[_id] = spans_b[_id]

        return set(spans.values())

    def get_consolidated_network_from_outcomes(
        self,
        outcomes: List[SpanComparisonOutcome],
    ) -> Network:
        """
        This method should be called after the user has been asked about all manual
        comparisons, and implements the results i.e. consolidating (or not) and adding
        to the consolidated network.

        Returns the consolidated Network.
        """
        spans = list(self._gather_spans_from_outcomes(outcomes))

        spans_layer, new_spans = self._create_qgis_layer_from_spans(spans)

        return Network(
            # at this point, nodes are the same for both networks
            nodes=self.network_a.nodes,
            spans=new_spans,
            nodesLayer=self.network_a.nodesLayer,
            spansLayer=spans_layer,
        )

    def _create_qgis_layer_from_spans(
        self, spans: List[Span]
    ) -> Tuple[QgsVectorLayer, List[Span]]:
        LAYER_NAME = "_ofds_consolidated_spans"

        project = QgsProject.instance()
        assert project

        # Remove an old intermediate layers from previous tool uses
        if len(project.mapLayersByName(LAYER_NAME)) > 0:
            project.removeMapLayers(
                [layer.id() for layer in project.mapLayersByName(LAYER_NAME)]
            )

        # Create the new QgsVectorLayer from consolidated Spans
        layer_uri = "LineString?crs=epsg:4326&index=yes"
        layer = QgsVectorLayer(layer_uri, LAYER_NAME, "memory")
        layer.setCustomProperty("skipMemoryLayersCheck", 1)

        layer_data = layer.dataProvider()
        assert layer_data

        fields = Span.get_qgs_fields()

        layer.startEditing()
        layer_data.addAttributes(fields.toList())
        layer.commitChanges()

        logger.debug(f"Adding {len(spans)} Spans to QgsVectorLayer")

        new_spans: List[Span] = list()

        # Create a new QgsFeature for each new Node, copying old Geometry + consolidated properties
        #  + new Nodes because featureId changes w/ a new layer
        for span in spans:
            new_feature = QgsFeature(fields)
            new_feature.setGeometry(span.featureGeometry)
            for field in fields:
                if field.name() in span.properties:
                    new_feature.setAttribute(
                        field.name(), span.properties[field.name()]
                    )
            layer_data.addFeature(new_feature)
            new_spans.append(
                Span(span.id, span.properties, new_feature.id(), new_feature.geometry())
            )

        layer.updateExtents()

        # TODO: Change visibility from True to False when we're not testing anymore
        #       or make it a setting?
        project.addMapLayer(layer, True)

        return (layer, new_spans)

    def _remap_network_b_span_node_ids(self, span: Span) -> Span:
        new_properties = span.properties.copy()
        p_start = new_properties["start"]
        p_end = new_properties["end"]

        if p_start["id"] in self.network_b_ids_map:
            p_start["id"] = self.network_b_ids_map[p_start["id"]]

        if p_end["id"] in self.network_b_ids_map:
            p_end["id"] = self.network_b_ids_map[p_end["id"]]

        new_properties["start"] = p_start
        new_properties["end"] = p_end

        new_span = Span(
            span.id,
            properties=new_properties,
            featureId=span.featureId,
            featureGeometry=span.featureGeometry,
        )
        return new_span
