from typing import List, Set, Tuple

from qgis.core import QgsVectorLayer, QgsProject

from .network import Node, Network
from .comparison import NodeComparison, ComparisonOutcome, ConsolidationReason


class NetworkNodesConsolidator:
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
                        primary_node=comparison.node_a,
                        secondary_node=comparison.node_b,
                        confidence=comparison.confidence,
                        matching_properties=matching_properties,
                        manual=False,
                    )
                    outcome = ComparisonOutcome(consolidate=reason)
                    self.nodes.append((reason.primary_node, outcome))

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
                self.nodes.append((outcome.consolidate.primary_node, outcome))

            else:
                # no match: keep both
                self.nodes.append((comparison.node_a, outcome))
                self.nodes.append((comparison.node_b, outcome))

    def get_consolidated_network(self):
        # TODO:
        # Create a new Qgs Layer out of the Consolidated nodes
        _ = qgis_layer_from_nodes(set([n for (n, o) in self.nodes]))


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


# TODO
class NetworkSpansConsolidator:
    nodes: List[Node]

    def __init__(self, nodes: List[Node]):
        self.nodes = nodes

    def update_spans(self):
        # TODO
        # after node comparision has been done, look through the start/ends of
        # spans and update any where duplicates were found and replaced
        pass

    def compare_spans(self):
        # TODO
        pass
