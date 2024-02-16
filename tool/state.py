from typing import ClassVar, TypeVar, Generic, List, Union, Tuple
from enum import Enum
from dataclasses import dataclass, field

from ..models import Feature, FeaturePairComparisonOutcome, Network, Node, Span


class ToolStateEnum(str, Enum):
    """
    Each state represents one of the stages in the tool flow.
    """

    READY_FOR_SELECTION = "READY_FOR_SELECTION"
    CONSOLIDATING_NODES = "CONSOLIDATING_NODES"
    CONSOLIDATING_SPANS = "CONSOLIDATING_SPANS"
    OUTPUT = "OUTPUT"


class AbstractToolState:
    state: ClassVar[ToolStateEnum]


class ToolLayerSelectState(AbstractToolState):
    state = ToolStateEnum.READY_FOR_SELECTION


FT = TypeVar("FT", bound=Feature)


@dataclass
class GenericToolComparisonState(Generic[FT], AbstractToolState):
    # Networks
    networks: Tuple[Network, Network]

    # Features for consolidation consolidation
    featurePairs: List[Tuple[FT, FT]]

    # Outcome for each pair,
    # outcomes is a list the same length as featurePairs, with all values initially None
    # but updated as outcomes are input by the user.
    outcomes: List[Union[None, FeaturePairComparisonOutcome]] = field(
        default_factory=list
    )

    # Keep track of which pair we're looking at now
    current: int = field(default=0)

    def __post_init__(self):
        # Create outcomes list the same length as featurePairs
        if len(self.outcomes) != len(self.featurePairs):
            self.outcomes = list(None for _ in self.featurePairs)

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
        return len(self.featurePairs)

    @property
    def nCompared(self) -> int:
        return len([o for o in self.outcomes if o is not None])

    @property
    def currentPair(self) -> Tuple[FT, FT]:
        return self.featurePairs[self.current]

    @property
    def currentOutcome(self) -> Union[None, FeaturePairComparisonOutcome]:
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
