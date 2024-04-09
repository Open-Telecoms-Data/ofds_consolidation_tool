from typing import ClassVar, List, Union, Tuple
from enum import Enum

from qgis.core import QgsVectorLayer

from ..model.consolidation import NetworkNodesConsolidator
from ..model.comparison import NodeComparison, ComparisonOutcome
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

    # Keep track of which pair we're looking at now
    current: int

    def __init__(
        self,
        networks: Tuple[Network, Network],
        nodes_consolidator: NetworkNodesConsolidator,
    ):
        self.networks = networks
        self.nodes_consolidator = nodes_consolidator
        self.current = 0

    def __str__(self):
        return f"<ToolNodeComparisonState total={self.nTotal} compared={self.nCompared} current={self.current}>"

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

    def setOutcome(self, outcome: ComparisonOutcome):
        if outcome.consolidate:
            self.nodes_consolidator.node_ask_outcomes[self.current] = outcome

    @property
    def nTotal(self) -> int:
        return len(self.nodes_consolidator.node_ask_comparisons)

    @property
    def nCompared(self) -> int:
        return len(
            [o for o in self.nodes_consolidator.node_ask_outcomes if o is not None]
        )

    @property
    def currentComparison(self) -> Union[None, NodeComparison]:
        try:
            return self.nodes_consolidator.node_ask_comparisons[self.current]
        except IndexError:
            return None

    @property
    def currentOutcome(self) -> Union[None, ComparisonOutcome]:
        try:
            return self.nodes_consolidator.node_ask_outcomes[self.current]
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
