from abc import ABC, abstractmethod
from typing import Dict, Generic, List, Set, Tuple, Type

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


class AbstractNetworkConsolidator(Generic[FeatureT, ComparisonT], ABC):

    FeatureCls: Type[FeatureT]

    PROPS_TO_COPY: List[str]
    PROPS_TO_MERGE_ARRAYS: List[str]
    PROPS_TO_SUM: List[str]
    PROPS_TO_CONCAT: List[str]

    network_b_ids_map: Dict[str, str]

    @abstractmethod
    def get_comparisons_to_ask_user(self) -> List[ComparisonT]: ...

    def _merge_features(self, primary: FeatureT, secondary: FeatureT) -> FeatureT:
        # Update span id map
        # Note that we only merge spans with the same start/end IDs
        self.network_b_ids_map[secondary.id] = primary.id

        # Merge properties
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

        return self.FeatureCls(
            primary.id, props, primary.featureId, primary.featureGeometry
        )


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

    nodes: List[Tuple[Node, NodeComparisonOutcome]]

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
        self.nodes = list()
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
                    # No chance of match, just add them both individually
                    self.nodes.append(
                        (
                            comparison.node_a,
                            NodeComparisonOutcome(
                                comparison=comparison,
                                consolidate=False,
                            ),
                        )
                    )
                    self.nodes.append(
                        (
                            comparison.node_b,
                            NodeComparisonOutcome(
                                comparison=comparison, consolidate=False
                            ),
                        )
                    )

                elif comparison.confidence >= self.merge_threshold:
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
                    assert isinstance(reason.primary, Node)
                    self.nodes.append((reason.primary, outcome))
                    self.network_b_ids_map[comparison.node_b.id] = comparison.node_a.id

                elif comparison.confidence >= self.ask_threshold:
                    #   todo: get user pref for which network to keep
                    #   todo: ability to merge rather than replace? (stretch goal)
                    self.user_comparisons.append(comparison)

    def get_comparisons_to_ask_user(self) -> List[NodeComparison]:
        return self.user_comparisons

    def finalise_with_user_comparison_outcomes(
        self,
        user_comparison_outcomes: List[Tuple[NodeComparison, NodeComparisonOutcome]],
    ):
        """
        This method should be called after the user has been asked about all manual
        comparisons, and implements the results i.e. consolidating (or not) and adding
        to the consolidated network.
        """
        for comparison, outcome in user_comparison_outcomes:
            # TODO: Add "provenance" property here
            if isinstance(outcome.consolidate, ConsolidationReason):
                assert isinstance(outcome.consolidate.primary, Node)
                assert isinstance(outcome.consolidate.secondary, Node)
                self.nodes.append(
                    (
                        self._merge_features(
                            outcome.consolidate.primary,
                            outcome.consolidate.secondary,
                        ),
                        outcome,
                    )
                )

            else:
                # no match: keep both
                self.nodes.append((comparison.node_a, outcome))
                self.nodes.append((comparison.node_b, outcome))

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
        qgs_layer, nodes = self._qgis_layer_from_nodes(
            set([n for (n, o) in self.nodes])
        )

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
        self, nodes: Set[Node]
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
        assert layer_data

        fields = Node.get_qgs_fields()

        layer.startEditing()
        layer_data.addAttributes(fields.toList())
        layer.commitChanges()

        logger.debug(f"Adding {len(nodes)} Nodes to QgsVectorLayer")

        new_nodes: List[Node] = list()

        # Create a new QgsFeature for each new Node, copying old Geometry + consolidated properties
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

    network_b_ids_map: Dict[str, str]

    def __init__(self, network_a: Network, network_b: Network):
        self.network_a = network_a
        self.network_b = network_b
        self.network_b_ids_map = dict()

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

        return matches

    def get_consolidated_network_with_user_comparison_outcomes(
        self,
        user_comparison_outcomes: List[SpanComparisonOutcome],
    ) -> Network:
        """
        This method should be called after the user has been asked about all manual
        comparisons, and implements the results i.e. consolidating (or not) and adding
        to the consolidated network.

        Returns the consolidated Network.https://github.com/Open-Telecoms-Data/ofds_consolidation_tool/tree/rg/spans-comparison-functionality
        """
        spans: List[Tuple[Span, SpanComparisonOutcome]] = list()

        for outcome in user_comparison_outcomes:
            # TODO: Add provenance property to each Span
            if isinstance(outcome.consolidate, ConsolidationReason):
                assert isinstance(outcome.consolidate.primary, Span)
                assert isinstance(outcome.consolidate.secondary, Span)
                spans.append(
                    (
                        self._merge_features(
                            outcome.consolidate.primary,
                            outcome.consolidate.secondary,
                        ),
                        outcome,
                    )
                )

            else:
                # no match: keep both
                spans.append((outcome.comparison.span_a, outcome))
                spans.append((outcome.comparison.span_b, outcome))

        nodes_layer = QgsVectorLayer()
        spans_layer = QgsVectorLayer()

        return Network(
            # at this point, nodes are the same for both networks
            nodes=self.network_a.nodes,
            spans=[s for (s, _) in spans],
            nodesLayer=nodes_layer,
            spansLayer=spans_layer,
        )

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
