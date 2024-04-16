from typing import ClassVar, List, Union, Tuple, cast
from enum import Enum


from qgis.core import QgsVectorLayer

from ..model.consolidation import NetworkNodesConsolidator
from ..model.comparison import ConsolidationReason, NodeComparison, ComparisonOutcome
from ..model.network import Network, Node
from ..view_warningbox import (
    show_node_incomplete_consolidation_warning,
    show_node_multi_consolidation_warning,
)


class ToolInvalidState(Exception):
    pass


class ToolStateEnum(str, Enum):
    """
    Each state represents one of the stages in the tool flow.
    """

    READY_FOR_SELECTION = "READY_FOR_SELECTION"
    COMPARING_NODES = "COMPARING_NODES"
    COMPARING_SPANS = "COMPARING_SPANS"
    OUTPUT = "OUTPUT"


class AbstractToolState:
    state: ClassVar[ToolStateEnum]


class ToolLayerSelectState(AbstractToolState):
    state = ToolStateEnum.READY_FOR_SELECTION
    selectableLayers: List[QgsVectorLayer]

    def __init__(self, selectableLayers: List[QgsVectorLayer]):
        self.selectableLayers = selectableLayers

    def __str__(self) -> str:
        return f"<ToolLayerSelectState n_layers={len(self.selectableLayers)}>"


class ToolNodeComparisonState(AbstractToolState):
    state = ToolStateEnum.COMPARING_NODES
    # Networks
    networks: Tuple[Network, Network]

    # Consolidator
    nodes_consolidator: NetworkNodesConsolidator
    comparisons_outcomes: List[Tuple[NodeComparison, Union[None, ComparisonOutcome]]]

    # Keep track of which pair we're looking at now
    current: int

    def __init__(
        self,
        networks: Tuple[Network, Network],
        nodes_consolidator: NetworkNodesConsolidator,
    ):
        self.networks = networks
        self.nodes_consolidator = nodes_consolidator
        self.comparisons_outcomes = [
            (comparison, None)
            for comparison in self.nodes_consolidator.get_comparisons_to_ask_user()
        ]
        self.current = 0

    def __str__(self):
        return (
            f"<ToolNodeComparisonState total={self.nTotal}"
            + f"compared={self.nCompared} current={self.current}>"
        )

    def gotoNextComparison(self):
        self.current += 1
        if self.current >= self.nTotal:
            self.current = 0

    def gotoPrevComparison(self):
        self.current -= 1
        if self.current < 0:
            self.current = self.nTotal - 1

    def setOutcomeConsolidate(self) -> bool:
        """
        Set the outcome of the current comparison as The Same aka Consolidate.
        Returns False if the user cancelled, True if was successful.
        """
        comparison = self.currentComparison
        assert comparison is not None

        # Find all other comparisons containing one of the now-consolidated nodes,
        # and set them to "Not Same", because we can only consolidate a node once.
        other_comparisons_with_node_a: List[Tuple[int, Node]] = list()
        other_comparisons_with_node_b: List[Tuple[int, Node]] = list()
        for other_i in range(len(self.comparisons_outcomes)):
            (other_comparison, other_outcome) = self.comparisons_outcomes[other_i]

            if comparison == other_comparison:
                continue

            if comparison.node_a.id == other_comparison.node_a.id:
                other_comparisons_with_node_a.append((other_i, other_comparison.node_b))

            elif comparison.node_b.id == other_comparison.node_b.id:
                other_comparisons_with_node_b.append((other_i, other_comparison.node_a))

        # Check that none of the other comparisons w/ overlapping nodes have already
        # been chosen to consolidate, if so display a warning to the user

        for other_i, other_node in other_comparisons_with_node_a:
            (other_comparison, other_outcome) = self.comparisons_outcomes[other_i]
            if other_outcome is not None and other_outcome.consolidate is not False:
                if not show_node_multi_consolidation_warning(
                    "A", comparison.node_a, other_node
                ):
                    return False

        for other_i, other_node in other_comparisons_with_node_b:
            (other_comparison, other_outcome) = self.comparisons_outcomes[other_i]
            if other_outcome is not None and other_outcome.consolidate is not False:
                if not show_node_multi_consolidation_warning(
                    "B", comparison.node_b, other_node
                ):
                    return False

        # If we've got this far, update all the other comparisons to be "not same"
        for other_i, _ in other_comparisons_with_node_a + other_comparisons_with_node_b:
            self.comparisons_outcomes[other_i] = (
                other_comparison,
                ComparisonOutcome(consolidate=False),
            )

        # Finally, update the outcome with a manual consolidation reason
        reason = ConsolidationReason(
            feature_type="NODE",
            primary_node=comparison.node_a,
            secondary_node=comparison.node_b,
            confidence=comparison.confidence,
            # TODO: user's choice of matching properties? User text message?
            matching_properties=comparison.get_high_scoring_properties(),
            manual=True,
        )

        self.comparisons_outcomes[self.current] = (
            comparison,
            ComparisonOutcome(consolidate=reason),
        )

        return True

    def setOutcomeDontConsolidate(self):
        comparison = self.currentComparison
        assert comparison is not None
        self.comparisons_outcomes[self.current] = (
            comparison,
            ComparisonOutcome(consolidate=False),
        )

    @property
    def nTotal(self) -> int:
        return len(self.comparisons_outcomes)

    @property
    def nCompared(self) -> int:
        return len(
            [1 for (_, outcome) in self.comparisons_outcomes if outcome is not None]
        )

    @property
    def all_compared(self) -> bool:
        return all(outcome is not None for (_, outcome) in self.comparisons_outcomes)

    @property
    def currentComparison(self) -> Union[None, NodeComparison]:
        try:
            return self.comparisons_outcomes[self.current][0]
        except IndexError:
            return None

    @property
    def currentOutcome(self) -> Union[None, ComparisonOutcome]:
        try:
            return self.comparisons_outcomes[self.current][1]
        except IndexError:
            return None

    def finish(self):
        if not self.all_compared:
            # If not all comparisons are complete, ask the user if they're sure they
            # want to finish.
            if not show_node_incomplete_consolidation_warning():
                # If they're not sure (clicked Cancel), let them continue comparing
                return self

            # If they're user, then set all unmarked comparisons to "don't consolidate"
            for i in range(len(self.comparisons_outcomes)):
                (comparison, outcome) = self.comparisons_outcomes[i]
                if outcome is None:
                    self.comparisons_outcomes[i] = (
                        comparison,
                        ComparisonOutcome(consolidate=False),
                    )

        self.nodes_consolidator.finalise_with_user_comparison_outcomes(
            cast(
                List[Tuple[NodeComparison, ComparisonOutcome]],
                self.comparisons_outcomes,
            )
        )

        consolidated_network = self.nodes_consolidator.get_consolidated_network()
        return ToolSpanComparisonState()


class ToolSpanComparisonState(AbstractToolState):
    state = ToolStateEnum.COMPARING_SPANS


class ToolOutputState(AbstractToolState):
    state = ToolStateEnum.OUTPUT


ToolState = Union[
    ToolLayerSelectState,
    ToolNodeComparisonState,
    ToolSpanComparisonState,
    ToolOutputState,
]
