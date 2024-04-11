import json

from enum import Enum
from typing import Any, Dict, List

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
    properties: Dict[str, Any]

    def __init__(self, feature: QgsFeature):
        self.feature = feature
        self.featureId = feature.id()
        self.properties = feature.attributeMap()
        if "id" not in self.properties or not isinstance(self.properties["id"], str):
            raise OFDSInvalidFeature
        self.id = self.properties["id"]

    def __hash__(self) -> int:
        # Enable Nodes/Spans to be put in a Set or Dict
        return hash(self.id)


class Node(Feature):
    featureType = FeatureType.NODE

    def __init__(self, feature: QgsFeature):
        super().__init__(feature)
        if not self.feature.geometry().type() == QgsWkbTypes.GeometryType.PointGeometry:
            raise OFDSInvalidFeature("Nodes layer must be PointGeometry")

    def get(self, k):
        """
        Override get to access the properties.
        Parses nested dicts again because QGIS sometimes can't handle them.
        (Whether or not it does depends on underlying libraraies, so we have to
        prepare for both eventualities.)
        Also some shortcuts to properties we know we're comparing.
        """
        if k.startswith("location/address"):
            location = self.properties.get("location", {})
            try:
                address = location.get("address", {})
            except AttributeError:
                location_json = json.loads(l)
                address = location_json.get("address")
            if address:
                if k == "location/address/country":
                    return address.get("country")
                if k == "location/address/streetAddress":
                    return address.get("streetAddress")
                if k == "location/address/postalCode":
                    return address.get("postalCode")
                if k == "location/address/region":
                    return address.get("region")
                if k == "location/address/locality":
                    return address.get("locality")
            else:
                return None
        if k == "phase/name":
            phase = self.properties.get("phase", {})
            try:
                return phase.get("name")
            except AttributeError:
                phase_json = json.loads(phase)
                return phase_json.get("name")
        if k == "physicalInfrastructureProvider":
            # Only compare name, id is irrelevant
            pip = self.properties.get("physicalInfrastructureProvider", {})
            try:
                return pip.get("name")
            except AttributeError:
                pip_json = json.loads(pip)
                return pip_json.get("name")
        if k == "networkProviders":
            # Return a list of the names in the array, as ids are irrelevant
            nps = self.properties.get("networkProviders", [])
            names = []
            try:
                for np in nps:
                    names.append(np.get("name"))
            except AttributeError:
                nps_json = json.loads(nps)
            return names

        return self.properties.get(k)

    def __str__(self):
        name = self.properties["name"] if "name" in self.properties else self.id
        return f"<Node {name}>"


class Span(Feature):
    featureType = FeatureType.SPAN

    def get(self, k):
        return self.properties.get(k)

    def __str__(self):
        name = self.properties["name"] if "name" in self.properties else self.id
        return f"<Span {name}>"


class Network:
    """
    Top-level container object for an OFDS Network, including the source data (nodes &
    spans layers), plus helper indexes.
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
