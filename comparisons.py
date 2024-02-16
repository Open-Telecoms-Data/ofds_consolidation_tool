from abc import ABC, abstractmethod
from typing import Set, Tuple

from .models import Network, Node, Span


class AbstractNetworkComparison(ABC):
    def __init__(self, networkA: Network, networkB: Network):
        self.networkA = networkA
        self.networkB = networkB

    @abstractmethod
    def findPotentialSameNodes(self) -> Set[Tuple[Node, Node]]: ...

    @abstractmethod
    def findPotentialSameSpans(self) -> Set[Tuple[Span, Span]]: ...


class FindNearestNodeComparison(AbstractNetworkComparison):

    def findPotentialSameNodes(self) -> Set[Tuple[Node, Node]]:
        nearestNodes = set()

        for aNode in self.networkA.nodes:
            bNodeId = self.networkB.nodesSpacialIndex.nearestNeighbor(
                aNode.feature.geometry().asPoint(), 1
            )[0]
            nearestNodes.add((aNode, self.networkB.nodesByFeatureId[bNodeId]))

        return nearestNodes

    def findPotentialSameSpans(self) -> Set[Tuple[Span, Span]]:
        return set()


COMPARISON_CLASSES = [FindNearestNodeComparison]
