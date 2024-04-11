from itertools import repeat
from typing import List, Optional
from dataclasses import dataclass

from .exceptions import ModelInvalidState

from .network import Node, Network
from .comparison import NodeComparison, ComparisonOutcome


@dataclass(frozen=True)
class ConsolidationReason:
    """
    When two features are merged, this represents the relevant metadata.
    ie. ids of the two features, the confidence score, and a list of the
    properties with high similarity as the rationale.
    """

    feature_type: str
    primary_node: Node
    secondary_node: Node
    confidence: float
    matching_properties: List[str]
    manual: bool = False


class NetworkNodesConsolidator:
    """
    Builder class to get the comparisons out of a pair of networks.
    """

    network_a: Network
    network_b: Network

    merge_threshold: int
    ask_threshold: int
    match_radius_km: float

    nodes: List[Node]
    # spans: List[Span]
    node_comparisons: List[NodeComparison]
    node_ask_comparisons: List[NodeComparison]
    node_ask_outcomes: List[Optional[ComparisonOutcome]]
    # span_comparisons: List[SpanComparison]
    provenance: List[ConsolidationReason]

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
        self.nodes = []
        self.node_comparisons = []
        self.node_ask_comparisons = []
        self.provenance = []

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
                comparison = NodeComparison(a_node, b_node)

                if comparison.confidence >= self.merge_threshold:
                    self._consolidate_node_pair(comparison, manual=False)

                elif comparison.confidence >= self.ask_threshold:
                    self.node_ask_comparisons.append(comparison)

        self.node_ask_outcomes = list(repeat(None, len(self.node_ask_comparisons)))

    def _consolidate_node_pair(self, comparison: NodeComparison, manual: bool):
        #   todo: get user pref for which network to keep
        #   todo: ability to merge rather than replace? (stretch goal)
        matching_properties = comparison.get_high_scoring_properties()
        reason = ConsolidationReason(
            feature_type="NODE",
            primary_node=comparison.node_a,
            secondary_node=comparison.node_b,
            confidence=comparison.confidence,
            matching_properties=matching_properties,
            manual=manual,
        )
        self.provenance.append(reason)
        if reason.primary_node not in self.nodes:
            self.nodes.append(reason.primary_node)

    def finalise_asked_nodes(self):
        """
        This method should be called after the user has been asked about all manual
        comparisons, and implements the results i.e. consolidating (or not) and adding
        to the consolidated network.
        """
        for i in range(len(self.node_ask_comparisons)):
            comparison: NodeComparison = self.node_ask_comparisons[i]
            should_consolidate = self.node_ask_outcomes[i]

            if should_consolidate is None:
                raise ModelInvalidState("Found unfinished nodes comparison")

            if should_consolidate:
                self._consolidate_node_pair(comparison, manual=True)
            else:
                # no match: keep both
                if comparison.node_a not in self.nodes:
                    self.nodes.append(comparison.node_a)
                if comparison.node_b not in self.nodes:
                    self.nodes.append(comparison.node_b)

    def count_comparisons(self):
        return len(self.node_comparisons)

    def count_merged(self):
        return len(self.provenance)


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
