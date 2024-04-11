from typing import ClassVar, List, Union, Tuple
from enum import Enum

from qgis.core import QgsVectorLayer

from ..model.consolidation import NetworkNodesConsolidator
from ..model.comparison import ConsolidationReason, NodeComparison, ComparisonOutcome
from ..model.network import Network


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
        new_current = self.current + 1
        if new_current >= self.nTotal:
            new_current = 0
        self.current = new_current

    def gotoPrevComparison(self):
        new_current = self.current - 1
        if self.current < 0:
            new_current = self.nTotal - 1
        self.current = new_current

    def setOutcomeConsolidate(self):
        comparison = self.currentComparison
        assert comparison is not None
        reason = ConsolidationReason(
            feature_type="NODE",
            primary_node=comparison.node_a,
            secondary_node=comparison.node_b,
            confidence=comparison.confidence,
            matching_properties=comparison.get_high_scoring_properties(),
            manual=True,
        )
        self.comparisons_outcomes[self.current] = (
            comparison,
            ComparisonOutcome(consolidate=reason),
        )

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
