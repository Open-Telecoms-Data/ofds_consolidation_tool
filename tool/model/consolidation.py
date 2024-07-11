import json
import logging
import uuid
from abc import ABC, abstractmethod
from typing import Dict, Generic, Iterable, List, Set, Tuple, Type

from .comparison import (
    NodeComparison,
    NodeComparisonOutcome,
    ConsolidationReason,
    SpanComparison,
    ComparisonT,
    SpanComparisonOutcome,
)
from .network import Node, Network, Span, FeatureT, Feature, NetworkDescription, OFDSInvalidFeature
from .properties import (
    NODES_PROPERTIES_MERGE_CONFIG,
    SPANS_PROPERTIES_MERGE_CONFIG,
    PropMergeOp,
    merge_features_properties,
    generate_provenance_data,
)
from .qgis_utils import (
    create_qgis_geojson_layer_from_nodes,
    create_qgis_geojson_layer_from_spans,
)

logger = logging.getLogger(__name__)


# TODO: sort by diagonal distance
class AbstractNetworkConsolidator(Generic[FeatureT, ComparisonT], ABC):
    FeatureCls: Type[Feature]

    PROPS_MERGE_CONFIG: List[Tuple[str, PropMergeOp]]

    new_ofds_network: NetworkDescription
    _next_feature_id: int

    # Lookup for ID's of nodes/spans after consolidation
    network_a_ids_map: Dict[str, str]
    network_b_ids_map: Dict[str, str]

    def __init__(self):
        self._next_feature_id = 1
        self.network_a_ids_map = dict()
        self.network_b_ids_map = dict()

    def allocate_new_feature_id(self) -> str:
        new_id = str(self._next_feature_id)
        self._next_feature_id += 1
        return new_id

    @abstractmethod
    def get_comparisons_to_ask_user(self) -> List[ComparisonT]: ...

    def _merge_features(self, primary: Feature, secondary: Feature, provenance: Dict,
                        new_network: NetworkDescription) -> Feature:
        # Create a new ID for this span
        # Update ID map to keep track of which IDs have been reassigned
        new_id = self.allocate_new_feature_id()
        self.network_a_ids_map[primary.id] = new_id
        self.network_b_ids_map[secondary.id] = new_id

        # Merge properties
        props = merge_features_properties(self.PROPS_MERGE_CONFIG, primary, secondary)

        # Add provenance data
        props["provenance"] = provenance

        # Create merged Feature
        return self.FeatureCls(
            "", props, primary.featureId, primary.featureGeometry, new_network
        ).with_new_id(new_id, ofds_network=new_network)


class NetworkNodesConsolidator(AbstractNetworkConsolidator[Node, NodeComparison]):
    """
    Builder class to get the comparisons out of a pair of networks.
    """

    FeatureCls = Node

    PROPS_MERGE_CONFIG = NODES_PROPERTIES_MERGE_CONFIG

    network_a: Network
    network_b: Network

    merge_threshold: int
    ask_threshold: int
    match_radius_km: float

    user_comparisons: List[NodeComparison]
    outcomes: List[NodeComparisonOutcome]

    def __init__(
            self,
            network_a: Network,
            network_b: Network,
            merge_above: int = 100,
            ask_above: int = 0,
            match_radius_km: float = 10.0,
    ):

        super().__init__()

        self.network_a = network_a
        self.network_b = network_b
        self.merge_threshold = merge_above
        self.ask_threshold = ask_above
        self.match_radius_km = match_radius_km
        self.outcomes = list()
        self.user_comparisons = []

        self.new_ofds_network = NetworkDescription(
            id=str(uuid.uuid4()),
            name=f"Consolidated Network of {network_a.ofds_network.name} and {network_b.ofds_network.name}"
        )

        self._compare_nodes()

    def _compare_nodes(self):
        """
        Create NodeComparisons, and check for either auto-merging or give to the UI to
        ask the user.
        """
        user_comparisons = list()

        for a_node in self.network_a.nodes:
            for b_node in self.network_b.nodes:
                comparison = NodeComparison(a_node, b_node)
                if comparison.distance_km > self.match_radius_km:
                    # No chance of match, just add immediate no-consolidate outcome
                    self.add_comparison_outcomes(
                        [
                            NodeComparisonOutcome(
                                comparison=comparison, consolidate=False
                            )
                        ]
                    )

                elif comparison.confidence > self.merge_threshold:
                    # Auto-consolidate
                    similar_fields = comparison.get_high_scoring_properties()
                    reason = ConsolidationReason(
                        feature_type="NODE",
                        primary=comparison.node_a,
                        secondary=comparison.node_b,
                        confidence=comparison.confidence,
                        similar_fields=similar_fields,
                        manual=False,
                    )
                    outcome = NodeComparisonOutcome(
                        comparison=comparison, consolidate=reason
                    )
                    self.add_comparison_outcomes([outcome])

                elif comparison.confidence >= self.ask_threshold:
                    #   todo: get user pref for which network to keep
                    user_comparisons.append(comparison)

        self.user_comparisons = user_comparisons

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

        # Create and gather consolidated nodes
        for outcome in outcomes:
            if isinstance(outcome.consolidate, ConsolidationReason):
                assert isinstance(outcome.consolidate.primary, Node)
                assert isinstance(outcome.consolidate.secondary, Node)

                provenance_data = generate_provenance_data(outcome.consolidate)

                consolidated_node = self._merge_features(
                    outcome.consolidate.primary,
                    outcome.consolidate.secondary,
                    provenance_data,
                    self.new_ofds_network,
                )
                logger.info(f"Creating consolidated node: {consolidated_node.name}")
                assert consolidated_node.id not in nodes
                assert isinstance(consolidated_node, Node)
                nodes[consolidated_node.id] = consolidated_node

        # Gather unconsolidated nodes from A
        for _id in unconsolidated_ids_a:
            new_id = self.allocate_new_feature_id()
            self.network_a_ids_map[_id] = new_id
            nodes[new_id] = nodes_a[_id].with_new_id(new_id, ofds_network=self.new_ofds_network)

        # Gather unconsolidated nodes from B, creating new IDs if there's a clash
        for _id in unconsolidated_ids_b:
            new_id = self.allocate_new_feature_id()
            self.network_b_ids_map[_id] = new_id
            nodes[new_id] = nodes_b[_id].with_new_id(new_id, ofds_network=self.new_ofds_network)

        return set(nodes.values())

    def _remap_span_node_ids(self, span: Span, lookup: Dict[str, str]) -> Span:
        new_properties = span.properties.copy()
        p_start = new_properties["start"].copy()
        p_end = new_properties["end"].copy()

        # Check in case properties have been loaded as nested JSON string
        if isinstance(p_start, str):
            p_start = json.loads(p_start)

        if isinstance(p_end, str):
            p_end = json.loads(p_end)

        try:
            p_start["id"] = lookup[p_start["id"]]
            p_end["id"] = lookup[p_end["id"]]
        except KeyError:
            raise OFDSInvalidFeature(f"Error: Span {span.id} has an invalid start/end")

        new_properties["start"] = p_start
        new_properties["end"] = p_end

        new_span = Span(
            span.id,
            properties=new_properties,
            featureId=span.featureId,
            featureGeometry=span.featureGeometry,
            ofds_network=self.new_ofds_network,
        )
        return new_span

    def get_networks_with_consolidated_nodes(self) -> Tuple[Network, Network]:
        nodes = list(self._gather_nodes_from_outcomes(self.outcomes))
        qgs_layer, nodes = create_qgis_geojson_layer_from_nodes(nodes)

        # Network A IDs never change, so no remapping needed
        new_network_a = Network(
            nodes=nodes,
            nodesLayer=qgs_layer,
            spans=list(self._remap_span_node_ids(span, lookup=self.network_a_ids_map) for span in self.network_a.spans),
            spansLayer=self.network_a.spansLayer,
            ofds_network=self.network_a.ofds_network,
        )

        # Network B span start/end IDs may be remapped
        new_network_b = Network(
            nodes=nodes,
            nodesLayer=qgs_layer,
            spans=list(self._remap_span_node_ids(span, lookup=self.network_b_ids_map) for span in self.network_b.spans),
            spansLayer=self.network_b.spansLayer,
            ofds_network=self.network_b.ofds_network,
        )

        return new_network_a, new_network_b


class NetworkSpansConsolidator(AbstractNetworkConsolidator[Span, SpanComparison]):
    FeatureCls = Span

    PROPS_MERGE_CONFIG = SPANS_PROPERTIES_MERGE_CONFIG

    network_a: Network
    network_b: Network

    matched_spans_in_a: Set[str]
    matched_spans_in_b: Set[str]

    comparison_outcomes: List[NodeComparisonOutcome]

    def __init__(self, network_a: Network, network_b: Network, new_ofds_network: NetworkDescription):
        super().__init__()

        self.network_a = network_a
        self.network_b = network_b
        self.matched_spans_in_a = set()
        self.matched_spans_in_b = set()
        self.comparison_outcomes = list()
        self.new_ofds_network = new_ofds_network

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

                provenance_data = generate_provenance_data(outcome.consolidate)

                consolidated_span = self._merge_features(
                    outcome.consolidate.primary,
                    outcome.consolidate.secondary,
                    provenance_data,
                    self.new_ofds_network,
                )
                logger.info(f"Creating consolidated span: {consolidated_span.name}")
                assert consolidated_span.id not in spans
                assert isinstance(consolidated_span, Span)
                spans[consolidated_span.id] = consolidated_span

        # Gather unconsolidated nodes from A
        for _id in unconsolidated_ids_a:
            new_id = self.allocate_new_feature_id()
            spans[new_id] = spans_a[_id].with_new_id(new_id, ofds_network=self.new_ofds_network)

        # Gather unconsolidated nodes from B, creating new IDs if there's a clash
        for _id in unconsolidated_ids_b:
            new_id = self.allocate_new_feature_id()
            spans[new_id] = spans_b[_id].with_new_id(new_id, ofds_network=self.new_ofds_network)

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

        spans_layer, new_spans = create_qgis_geojson_layer_from_spans(spans)

        return Network(
            # at this point, nodes are the same for both networks
            nodes=self.network_a.nodes,
            spans=new_spans,
            nodesLayer=self.network_a.nodesLayer,
            spansLayer=spans_layer,
            ofds_network=self.new_ofds_network,
        )