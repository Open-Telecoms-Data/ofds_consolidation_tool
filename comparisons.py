from dataclasses import dataclass
from typing import ClassVar, Generic, Optional, Set, Tuple, TypeVar

from .models import FeatureType, Network, Node, Span


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


#
# Nodes
#


@dataclass(frozen=True)
class NodeComparison:
    featureType = FeatureType.NODE
    features: Tuple[Node, Node]
    reason: ComparisonReason


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


@dataclass(frozen=True)
class SpanComparison:
    featureType = FeatureType.SPAN
    features: Tuple[Span, Span]
    reason: ComparisonReason


def compareSpans(networkA: Network, networkB: Network) -> Set[SpanComparison]:
    # At this point, both networks share the same nodes