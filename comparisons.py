from dataclasses import dataclass
from typing import Generic, Optional, Set, Tuple, TypeVar

from .models import Network, Node, Span


@dataclass(frozen=True)
class ComparisonReason:
    """
    Description of the reason for two features to be compaired.
    """

    # Short slug name
    short_name: str

    # Human readable description
    description: str

    # Optional confidence score between 0 and 1
    confidence: Optional[float] = None


FT = TypeVar("FT", Node, Span)


@dataclass(frozen=True)
class GenericFeatureComparison(Generic[FT]):
    features: Tuple[FT, FT]
    reason: ComparisonReason


#
# Nodes
#

NodeComparison = GenericFeatureComparison[Node]


def compareNearestNodes(networkA: Network, networkB: Network) -> Set[NodeComparison]:
    reason = ComparisonReason(
        short_name="NEAREST_NODE",
        description="For each node in network A, find the nearest node in network B.",
    )

    comparisons: Set[NodeComparison] = set()

    for aNode in networkA.nodes:
        bNodeId = networkB.nodesSpacialIndex.nearestNeighbor(
            aNode.feature.geometry().asPoint(), 1
        )[0]
        comparisons.add(
            NodeComparison(
                features=(aNode, networkB.nodesByFeatureId[bNodeId]), reason=reason
            )
        )

    return comparisons


def compareNodes(networkA: Network, networkB: Network) -> Set[NodeComparison]:
    """
    Return a set of NodeComparisons based on all available heuristics.
    """

    # So far just nearest nodes
    return compareNearestNodes(networkA, networkB)


#
# Spans
#

SpanComparison = GenericFeatureComparison[Span]

# TODO
