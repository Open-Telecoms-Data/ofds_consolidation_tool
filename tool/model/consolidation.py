from abc import ABC, abstractmethod
from typing import Dict, Generic, List, Set, Tuple, TypeVar

import json

from qgis.core import QgsVectorLayer, QgsProject

from .network import Node, Network, Span
from .comparison import (
    NodeComparison,
    ComparisonOutcome,
    ConsolidationReason,
    SpanComparison,
)


ComparisonT = TypeVar("ComparisonT", NodeComparison, SpanComparison)


class AbstractNetworkConsolidator(Generic[ComparisonT], ABC):
    @abstractmethod
    def get_comparisons_to_ask_user(self) -> List[ComparisonT]: ...


class NetworkNodesConsolidator(AbstractNetworkConsolidator[NodeComparison]):
    """
    Builder class to get the comparisons out of a pair of networks.
    """

    network_a: Network
    network_b: Network

    merge_threshold: int
    ask_threshold: int
    match_radius_km: float

    user_comparisons: List[NodeComparison]

    nodes: List[Tuple[Node, ComparisonOutcome]]

    # Lookup for Id's of nodes from Network B after consolidation
    network_b_node_ids_map: Dict[str, str]

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
        self.network_b_node_ids_map = dict()

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
                        (comparison.node_a, ComparisonOutcome(consolidate=False))
                    )
                    self.nodes.append(
                        (comparison.node_b, ComparisonOutcome(consolidate=False))
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
                    outcome = ComparisonOutcome(consolidate=reason)
                    self.nodes.append((reason.primary, outcome))
                    self.network_b_node_ids_map[comparison.node_b.id] = (
                        comparison.node_a.id
                    )

                elif comparison.confidence >= self.ask_threshold:
                    #   todo: get user pref for which network to keep
                    #   todo: ability to merge rather than replace? (stretch goal)
                    self.user_comparisons.append(comparison)

    def get_comparisons_to_ask_user(self) -> List[NodeComparison]:
        return self.user_comparisons

    def finalise_with_user_comparison_outcomes(
        self, user_comparison_outcomes: List[Tuple[NodeComparison, ComparisonOutcome]]
    ):
        """
        This method should be called after the user has been asked about all manual
        comparisons, and implements the results i.e. consolidating (or not) and adding
        to the consolidated network.
        """
        for comparison, outcome in user_comparison_outcomes:
            if isinstance(outcome.consolidate, ConsolidationReason):
                self.nodes.append((outcome.consolidate.primary, outcome))
                self.network_b_node_ids_map[comparison.node_b.id] = comparison.node_a.id

            else:
                # no match: keep both
                self.nodes.append((comparison.node_a, outcome))
                self.nodes.append((comparison.node_b, outcome))

    def get_networks_with_consolidated_nodes(self) -> Tuple[Network, Network]:
        qgs_layer = qgis_layer_from_nodes(set([n for (n, o) in self.nodes]))

        def _remap_network_b_span_node_ids(span: Span) -> Span:
            new_properties = span.properties.copy()
            p_start = new_properties["start"]
            p_end = new_properties["end"]

            # Check in case properties have been loaded as nested JSON string
            if isinstance(p_start, str):
                p_start = json.loads(p_start)

            if isinstance(p_end, str):
                p_end = json.loads(p_end)

            if p_start["id"] in self.network_b_node_ids_map:
                p_start["id"] = self.network_b_node_ids_map[p_start["id"]]

            if p_end["id"] in self.network_b_node_ids_map:
                p_end["id"] = self.network_b_node_ids_map[p_end["id"]]

            new_properties["start"] = p_start
            new_properties["end"] = p_end

            new_span = Span(span.id, properties=new_properties, feature=span.feature)
            return new_span

        # Network A IDs never change, so no remapping needed
        new_network_a = Network(
            nodes=[n for (n, _) in self.nodes],
            nodesLayer=qgs_layer,
            spans=self.network_a.spans,
            spansLayer=self.network_a.spansLayer,
        )

        # Network B span start/end IDs may be remapped
        new_network_b = Network(
            nodes=[n for (n, _) in self.nodes],
            nodesLayer=qgs_layer,
            spans=list(
                _remap_network_b_span_node_ids(span) for span in self.network_b.spans
            ),
            spansLayer=self.network_b.spansLayer,
        )

        return (new_network_a, new_network_b)


def qgis_layer_from_nodes(nodes: Set[Node]) -> QgsVectorLayer:
    LAYER_NAME = "_ofds_consolidated_nodes"

    # TODO: Tidy up (i.e. remove) this layer after we're done
    layer_uri = "Point?crs=epsg:4326&index=yes"
    layer = QgsVectorLayer(layer_uri, LAYER_NAME, "memory")
    layer.setCustomProperty("skipMemoryLayersCheck", 1)
    driver = layer.dataProvider()
    assert driver

    for node in nodes:
        driver.addFeature(node.feature)

    project = QgsProject.instance()
    assert project

    # Remove an old intermediate layers from previous tool uses
    if len(project.mapLayersByName(LAYER_NAME)) > 0:
        project.removeMapLayers([LAYER_NAME])

    # TODO: Change visibility from True to False when we're not testing anymore
    project.addMapLayer(layer, True)

    return layer


class NetworkSpansConsolidator(AbstractNetworkConsolidator[SpanComparison]):
    network_a: Network
    network_b: Network

    def __init__(self, network_a: Network, network_b: Network):
        self.network_a = network_a
        self.network_b = network_b

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

    def finalise_with_user_comparison_outcomes(
        self, user_comparison_outcomes: List[Tuple[NodeComparison, ComparisonOutcome]]
    ):
        raise NotImplementedError
