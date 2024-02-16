from enum import Enum
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from qgis.core import QgsFeature, QgsSpatialIndex, QgsVectorLayer, QgsWkbTypes


class OFDSInvalidFeature(Exception):
    pass


class FeatureType(str, Enum):
    NODE = "NODE"
    SPAN = "SPAN"


class Feature:
    """
    A Node or Span.
    Wrapper around an OFDS-compliant QgsFeature.
    """

    feature: QgsFeature
    featureId: int  # featureId is the QGIS-internal Id
    featureType: FeatureType
    id: str  # id is the OFDS id
    data: Dict[str, Any]

    def __init__(self, feature: QgsFeature):
        self.feature = feature
        self.featureId = feature.id()
        self.data = feature.attributeMap()
        if "id" not in self.data or not isinstance(self.data["id"], str):
            raise OFDSInvalidFeature
        self.id = self.data["id"]


class Node(Feature):
    featureType = FeatureType.NODE

    def __init__(self, feature: QgsFeature):
        super().__init__(feature)
        if not self.feature.geometry().type() == QgsWkbTypes.GeometryType.PointGeometry:
            raise OFDSInvalidFeature("Nodes layer must be PointGeometry")

    def __str__(self):
        name = self.data["name"] if "name" in self.data else self.id
        return f"<Node {name}>"


class Span(Feature):
    featureType = FeatureType.SPAN

    def __str__(self):
        name = self.data["name"] if "name" in self.data else self.id
        return f"<Span {name}>"


class Network:
    """
    Top-level container object for an OFDS Network, including the source data (nodes & spans layers), plus helper indexes.
    """

    nodesLayer: QgsVectorLayer
    spansLayer: QgsVectorLayer

    nodes: List[Node]
    spans: List[Span]

    # featureId is the QGIS-internal lookup Id
    nodesByFeatureId: Dict[int, Node]
    spansByFeatureId: Dict[int, Span]

    # nodeId/spanId is the OFDS Id
    nodesByNodeId: Dict[str, Node]
    spansBySpanId: Dict[str, Span]

    nodesSpacialIndex: QgsSpatialIndex
    spansSpacialIndex: QgsSpatialIndex

    def __init__(self, nodesLayer: QgsVectorLayer, spansLayer: QgsVectorLayer):
        self.nodesLayer = nodesLayer
        self.spansLayer = spansLayer

        # Load in all the nodes/spans from layer features
        self.nodes = list(map(Node, list(self.nodesLayer.getFeatures())))  # type: ignore
        self.spans = list(map(Span, list(self.nodesLayer.getFeatures())))  # type: ignore

        self.nodesByFeatureId = {n.featureId: n for n in self.nodes}
        self.spansByFeatureId = {s.featureId: s for s in self.spans}

        self.nodesByNodeId = {n.id: n for n in self.nodes}
        self.spansBySpanId = {s.id: s for s in self.spans}

        self.nodesSpacialIndex = QgsSpatialIndex(self.nodesLayer.getFeatures())
        self.spansSpacialIndex = QgsSpatialIndex(self.spansLayer.getFeatures())


@dataclass(frozen=True)
class FeatureComparisonOutcome:
    """
    Represents the outcome of the comparison of two nodes.
    """

    areDuplicate: bool
    reason: Optional[str]
