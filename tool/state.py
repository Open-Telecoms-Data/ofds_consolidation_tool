from typing import ClassVar, TypeVar, Generic, List, Union, Tuple
from enum import Enum

from qgis.core import QgsVectorLayer

from ..comparisons import GenericFeatureComparison
from ..models import FeatureComparisonOutcome, Network, Node, Span


class ToolInvalidState(Exception):
    pass


class ToolStateEnum(str, Enum):
    """
    Each state represents one of the stages in the tool flow.
    """

    READY_FOR_SELECTION = "READY_FOR_SELECTION"
    GATHERING_NODE_COMPARISONS = "GATHERING_NODE_COMPARISONS"
    CONSOLIDATING_NODES = "CONSOLIDATING_NODES"
    GATHERING_SPAN_COMPARISONS = "GATHERING_SPAN_COMPARISONS"
    CONSOLIDATING_SPANS = "CONSOLIDATING_SPANS"
    OUTPUT = "OUTPUT"


class AbstractToolState:
    state: ClassVar[ToolStateEnum]


class ToolLayerSelectState(AbstractToolState):
    state = ToolStateEnum.READY_FOR_SELECTION
    selectableLayers: List[QgsVectorLayer]

    def __init__(self, selectableLayers: List[QgsVectorLayer]):
        self.selectableLayers = selectableLayers


FT = TypeVar("FT", Node, Span)


class GenericToolComparisonState(Generic[FT], AbstractToolState):
    # Networks
    networks: Tuple[Network, Network]

    # Features for consolidation comparison
    comparisons: List[GenericFeatureComparison[FT]]

    # Outcome for each comparison,
    # outcomes is a list the same length as comparisons, with all values initially None
    # but updated as outcomes are input by the user.
    outcomes: List[Union[None, FeatureComparisonOutcome]]

    # Keep track of which pair we're looking at now
    current: int

    def __init__(
        self,
        networks: Tuple[Network, Network],
        comparisons: List[GenericFeatureComparison[FT]],
    ):
        if len(comparisons) < 1:
            # FIXME: Is 0 comparisons ever valid? Should be allowed? Jump straight to output?
            raise ToolInvalidState

        self.networks = networks
        self.comparisons = comparisons
        self.current = 0

        # Create outcomes list the same length as featurePairs
        self.outcomes = list(None for _ in self.comparisons)

    def next(self):
        new_current = self.current + 1
        if new_current >= self.nTotal:
            new_current = 0
        self.current = new_current

    def prev(self):
        new_current = self.current - 1
        if self.current < 0:
            new_current = self.nTotal - 1
        self.current = new_current

    @property
    def nTotal(self) -> int:
        return len(self.comparisons)

    @property
    def nCompared(self) -> int:
        return len([o for o in self.outcomes if o is not None])

    @property
    def currentComparison(self) -> GenericFeatureComparison[FT]:
        return self.comparisons[self.current]

    @property
    def currentOutcome(self) -> Union[None, FeatureComparisonOutcome]:
        return self.outcomes[self.current]


class ToolNodeComparisonState(GenericToolComparisonState[Node]):
    state = ToolStateEnum.CONSOLIDATING_NODES


class ToolSpanComparisonState(GenericToolComparisonState[Span]):
    state = ToolStateEnum.CONSOLIDATING_SPANS


class ToolOutputState(AbstractToolState):
    state = ToolStateEnum.OUTPUT


ToolState = Union[
    ToolLayerSelectState,
    ToolNodeComparisonState,
    ToolSpanComparisonState,
    ToolOutputState,
]
