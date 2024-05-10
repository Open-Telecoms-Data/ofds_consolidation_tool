import logging
from abc import abstractmethod
from typing import ClassVar, Generic, List, Type, Union, Tuple, cast
from enum import Enum


from qgis.core import QgsVectorLayer

from ..model.settings import Settings

from ..model.consolidation import (
    ComparisonT,
    NetworkNodesConsolidator,
    NetworkSpansConsolidator,
    AbstractNetworkConsolidator,
)

from ..model.comparison import (
    ComparisonOutcome,
    ConsolidationReason,
    NodeComparison,
    NodeComparisonOutcome,
    SpanComparison,
    SpanComparisonOutcome,
)

from ..model.network import Network, Node, Span, FeatureT
from ..view_warningbox import (
    show_node_incomplete_consolidation_warning,
    show_multi_consolidation_warning,
    show_warningbox,
)

logger = logging.getLogger(__name__)


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


class AbstractToolComparisonState(Generic[FeatureT, ComparisonT], AbstractToolState):
    ComparisonOutcomeCls: Type[ComparisonOutcome[ComparisonT]]

    # Global Settings
    settings: Settings

    # Networks
    networks: Tuple[Network, Network]

    # Consolidator
    consolidator: AbstractNetworkConsolidator[FeatureT, ComparisonT]
    comparisons_outcomes: List[
        Tuple[ComparisonT, Union[None, ComparisonOutcome[ComparisonT]]]
    ]

    # Keep track of which pair we're looking at now
    current: int

    def __init__(
        self,
        networks: Tuple[Network, Network],
        consolidator: AbstractNetworkConsolidator[FeatureT, ComparisonT],
        settings: Settings,
    ):
        self.settings = settings
        self.networks = networks
        self.consolidator = consolidator
        self.comparisons_outcomes = [
            (comparison, None)
            for comparison in self.consolidator.get_comparisons_to_ask_user()
        ]
        self.current = 0

    def __str__(self):
        return (
            f"<ToolComparisonState state={self.state} total={self.nTotal}"
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

    @abstractmethod
    def finish(self) -> "ToolState": ...

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
    def currentComparison(self) -> Union[None, ComparisonT]:
        try:
            return self.comparisons_outcomes[self.current][0]
        except IndexError:
            return None

    @property
    def currentOutcome(self) -> Union[None, ComparisonOutcome[ComparisonT]]:
        try:
            return self.comparisons_outcomes[self.current][1]
        except IndexError:
            return None

    def setOutcomeConsolidate(self) -> bool:
        """
        Set the outcome of the current comparison as The Same aka Consolidate.
        Returns False if the user cancelled, True if was successful.
        """
        comparison = self.currentComparison
        assert comparison is not None

        # Find all other comparisons containing one of the now-consolidated features,
        # and set them to "Not Same", because we can only consolidate a node once.
        other_comparisons_with_span_a: List[Tuple[int, FeatureT]] = list()
        other_comparisons_with_span_b: List[Tuple[int, FeatureT]] = list()

        for other_i in range(len(self.comparisons_outcomes)):
            (other_comparison, other_outcome) = self.comparisons_outcomes[other_i]

            if comparison == other_comparison:
                continue

            if comparison.feature_a.id == other_comparison.feature_a.id:
                other_comparisons_with_span_a.append(
                    (other_i, other_comparison.feature_b)
                )

            elif comparison.feature_b.id == other_comparison.feature_b.id:
                other_comparisons_with_span_b.append(
                    (other_i, other_comparison.feature_a)
                )

        # Check that none of the other comparisons w/ overlapping nodes have already
        # been chosen to consolidate, if so display a warning to the user

        for other_i, other_span in other_comparisons_with_span_a:
            (other_comparison, other_outcome) = self.comparisons_outcomes[other_i]
            if other_outcome is not None and other_outcome.consolidate is not False:
                if not show_multi_consolidation_warning(
                    "A", comparison.feature_a, other_span
                ):
                    return False

        for other_i, other_span in other_comparisons_with_span_b:
            (other_comparison, other_outcome) = self.comparisons_outcomes[other_i]
            if other_outcome is not None and other_outcome.consolidate is not False:
                if not show_multi_consolidation_warning(
                    "B", comparison.feature_b, other_span
                ):
                    return False

        # If we've got this far, update all the other comparisons to be "not same"
        for other_i, _ in other_comparisons_with_span_a + other_comparisons_with_span_b:
            self.comparisons_outcomes[other_i] = (
                other_comparison,
                self.ComparisonOutcomeCls(
                    comparison=other_comparison, consolidate=False
                ),
            )

        # Finally, update the outcome with a manual consolidation reason
        reason = ConsolidationReason(
            feature_type="NODE",
            primary=comparison.feature_a,
            secondary=comparison.feature_b,
            confidence=comparison.confidence,
            # TODO: user's choice of matching properties? User text message?
            matching_properties=comparison.get_high_scoring_properties(),
            manual=True,
        )

        self.comparisons_outcomes[self.current] = (
            comparison,
            self.ComparisonOutcomeCls(comparison=comparison, consolidate=reason),
        )

        return True

    def setOutcomeDontConsolidate(self):
        comparison = self.currentComparison
        assert comparison is not None
        self.comparisons_outcomes[self.current] = (
            comparison,
            self.ComparisonOutcomeCls(comparison=comparison, consolidate=False),
        )


class ToolNodeComparisonState(AbstractToolComparisonState[Node, NodeComparison]):
    state = ToolStateEnum.COMPARING_NODES
    ComparisonOutcomeCls = NodeComparisonOutcome

    consolidator: NetworkNodesConsolidator

    def __init__(
        self,
        networks: Tuple[Network, Network],
        settings: Settings,
    ):

        consolidator = NetworkNodesConsolidator(
            networks[0],
            networks[1],
            merge_above=settings.nodes_merge_threshold,
            ask_above=settings.nodes_ask_threshold,
            match_radius_km=settings.nodes_match_radius_km,
        )
        super().__init__(
            networks=networks, consolidator=consolidator, settings=settings
        )

    def finish(self) -> "ToolState":
        if not self.all_compared:
            # If not all comparisons are complete, ask the user if they're sure they
            # want to finish.
            if not show_node_incomplete_consolidation_warning():
                # If they're not sure (clicked Cancel), let them continue comparing
                return self

        # Gather outcomes, setting all all unmarked comparisons to "don't consolidate"
        outcomes: List[NodeComparisonOutcome] = list(
            o if o is not None else ComparisonOutcome(comparison=c, consolidate=False)
            for (c, o) in self.comparisons_outcomes
        )

        self.consolidator.add_comparison_outcomes(outcomes)

        (new_network_a, new_network_b) = (
            self.consolidator.get_networks_with_consolidated_nodes()
        )

        span_comparison_state = ToolSpanComparisonState(
            networks=(new_network_a, new_network_b),
            settings=self.settings,
        )

        if span_comparison_state.nTotal < 1:
            logger.warn("There are no Span Comparisons to be made!")
            show_warningbox(
                "No Spans to Compare",
                "No Spans are elegible for comparison!",
            )
            return span_comparison_state.finish()

        else:
            return span_comparison_state


class ToolSpanComparisonState(AbstractToolComparisonState[Span, SpanComparison]):
    state = ToolStateEnum.COMPARING_SPANS
    ComparisonOutcomeCls = SpanComparisonOutcome

    consolidator: NetworkSpansConsolidator

    def __init__(
        self,
        networks: Tuple[Network, Network],
        settings: Settings,
    ):
        consolidator = NetworkSpansConsolidator(
            network_a=networks[0],
            network_b=networks[1],
        )

        super().__init__(
            networks=networks, consolidator=consolidator, settings=settings
        )

    def finish(self) -> "ToolState":
        if not self.all_compared:
            show_warningbox(
                "Not all spans compared",
                "Please finish comparing spans before proceeding to output",
            )
            return self

        outcomes: List[SpanComparisonOutcome] = [
            cast(SpanComparisonOutcome, outcome)
            for (_, outcome) in self.comparisons_outcomes
            if outcome
        ]

        return ToolOutputState(
            network=self.consolidator.get_consolidated_network_from_outcomes(outcomes)
        )


class ToolOutputState(AbstractToolState):
    state = ToolStateEnum.OUTPUT

    output_network: Network

    def __init__(self, network: Network) -> None:
        self.output_network = network


ToolState = Union[
    ToolLayerSelectState,
    ToolNodeComparisonState,
    ToolSpanComparisonState,
    ToolOutputState,
]
