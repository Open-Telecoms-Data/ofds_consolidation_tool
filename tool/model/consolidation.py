from typing import List, Set, Tuple

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

    nodes: Set[Tuple[Node, ComparisonOutcome]]

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
        self.nodes = set()
        self.user_comparisons = []

        self._compare_nodes()

    def _compare_nodes(self):
        """
        Create NodeComparisons, and check for either auto-merging or give to the UI to
        ask the user.
        """
        # TODO - this compares every node with every other node
        # - needs replacing with code to only compare to nearest neighbours instead

        for a_node in self.network_a.nodes:
            for b_node in self.network_b.nodes:
                # TODO: Check distance here
                comparison = NodeComparison(a_node, b_node)

                if comparison.confidence >= self.merge_threshold:
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
                    self.nodes.add((reason.primary_node, outcome))

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
                self.nodes.add((outcome.consolidate.primary_node, outcome))

            else:
                # no match: keep both
                self.nodes.add((comparison.node_a, outcome))
                self.nodes.add((comparison.node_b, outcome))

    def get_consolidated_network(self):
        # TODO
        raise NotImplementedError


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
