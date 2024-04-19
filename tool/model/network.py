import json

from enum import Enum
from typing import Any, Dict, List, cast

from qgis.core import QgsFeature, QgsSpatialIndex, QgsVectorLayer, QgsWkbTypes


NESTED_PROPERTIES = [
    "end",
    "internationalConnections",
    "location",
    "network",
    "networkProviders",
    "phase",
    "physicalInfrastructureProvider",
    "start",
    "supplier"
]


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

    @classmethod
    def from_qgis_feature(cls, feature: QgsFeature):
        attributes = feature.attributeMap()
        
        # Check if nested objects have been loaded by QGIS, and load them if not.
        properties = {}
        for attribute in attributes.keys():
            if attribute in NESTED_PROPERTIES and isinstance(attributes.get(attribute), str):
                properties[attribute] = json.loads(attributes.get(attribute))
            else:
                properties[attribute] = attributes.get(attribute)

        if "id" not in properties or not isinstance(properties["id"], str):
            raise OFDSInvalidFeature
        ofds_id = properties["id"]
        return cls(id=ofds_id, properties=properties, feature=feature)

    def __init__(self, id: str, properties: Dict[str, Any], feature: QgsFeature):
        self.id = id
        self.properties = properties
        self.feature = feature
        self.featureId = self.feature.id()

        if (
            self.featureType == FeatureType.NODE
            and not self.feature.geometry().type()
            == QgsWkbTypes.GeometryType.PointGeometry
        ):
            raise OFDSInvalidFeature("Nodes layer must be PointGeometry")

        if (
            self.featureType == FeatureType.SPAN
            and not self.feature.geometry().type()
            == QgsWkbTypes.GeometryType.LineGeometry
        ):
            raise OFDSInvalidFeature("Spans layer must be LineGeometry")

    def __hash__(self) -> int:
        # Enable Nodes/Spans to be put in a Set or Dict
        return hash((self.id, self.featureId, self.featureType))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Feature):
            return self.id == other.id
        else:
            raise ValueError("Can't compare Feature to non-Feature")


class Node(Feature):
    featureType = FeatureType.NODE

    def get(self, k):
        """
        Override get to access the properties.
        Also some shortcuts to properties we know we're comparing.
        """
        if k.startswith("location/address"):
            location = self.properties.get("location", {})
            address = location.get("address", {})
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

        if k == "coordinates":
            return self.feature.geometry().asPoint().toString()

        if k == "phase/name":
            phase = self.properties.get("phase", {})
            return phase.get("name")

        if k == "physicalInfrastructureProvider":
            # Only compare name, id is irrelevant
            pip = self.properties.get("physicalInfrastructureProvider", {})
            return pip.get("name")

        if k == "networkProviders":
            # Return a list of the names in the array, as other properties are irrelevant
            nps = self.properties.get("networkProviders")
            names = []
            for np in nps:
                names.append(np.get("name"))
            return names

        if k.startswith("internationalConnections/"):
            ics = self.properties.get("internationalConnections", [])
            addresses = []
            regions = []
            countries = []
            localities = []
            postcodes = []
            for ic in ics:
                addresses.append(ic.get("streetAddress"))
                regions.append(ic.get("region"))
                countries.append(ic.get("country"))
                localities.append(ic.get("locality"))
                postcodes.append(ic.get("postalCode"))

            if k == "internationalConnections/streetAddress":
                return addresses
            if k == "internationalConnections/region":
                return regions
            if k == "internationalConnections/country":
                return countries
            if k == "internationalConnections/postalCode":
                return postcodes
            if k == "internationalConnections/locality":
                return localities

        return self.properties.get(k)

    @property
    def name(self) -> str:
        """Human readable name"""
        return cast(str, self.properties.get("name", self.id))

    def __str__(self):
        return f"<Node {self.name}>"


class Span(Feature):
    featureType = FeatureType.SPAN

    def get(self, k):
        """
        Override get to access the properties.
        Also some shortcuts to properties we know we're comparing.
        """
        if k == "start":
            # Return only id and coordinates
            start = self.properties.get("start", {})
            start_id = start.get("id")
            start_location = start.get("location", {}).get("coordinates")
            return { "id": start_id, "coordinates": start_location }

        if k == "end":
            # Return only id and coordinates
            end = self.properties.get("end", {})
            end_id = end.get("id")
            end_location = end.get("location", {}).get("coordinates")
            return { "id": end_id, "coordinates": end_location }

        if k == "phase/name":
            phase = self.properties.get("phase", {})
            return phase.get("name")

        if k == "physicalInfrastructureProvider":
            # Only compare name, id is irrelevant
            pip = self.properties.get("physicalInfrastructureProvider", {})
            return pip.get("name")

        if k == "networkProviders":
            # Return a list of the names in the array, as other properties are irrelevant
            nps = self.properties.get("networkProviders")
            names = []
            for np in nps:
                names.append(np.get("name"))
            return names

        if k == "supplier":
            # Only compare name, id is irrelevant
            supplier = self.properties.get("supplier", {})
            return supplier.get("name")

        return self.properties.get(k)

    @property
    def start_id(self):
        start_obj = self.properties["start"]
        if isinstance(start_obj, str):
            start_obj = json.loads(start_obj)
        return start_obj["id"]

    @property
    def end_id(self):
        end_obj = self.properties["end"]
        if isinstance(end_obj, str):
            end_obj = json.loads(end_obj)
        return end_obj["id"]

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

    @classmethod
    def from_qgs_vectorlayers(
        cls, nodesLayer: QgsVectorLayer, spansLayer: QgsVectorLayer
    ):
        # Load in all the nodes/spans from layer features
        nodes = list(map(Node.from_qgis_feature, list(nodesLayer.getFeatures())))  # type: ignore
        spans = list(map(Span.from_qgis_feature, list(spansLayer.getFeatures())))  # type: ignore

        return cls(
            nodes=nodes, nodesLayer=nodesLayer, spans=spans, spansLayer=spansLayer
        )

    def __init__(
        self,
        nodes: List[Node],
        nodesLayer: QgsVectorLayer,
        spans: List[Span],
        spansLayer: QgsVectorLayer,
    ):
        self.nodesLayer = nodesLayer
        self.spansLayer = spansLayer

        self.nodes = nodes
        self.spans = spans

        self.nodesByFeatureId = {n.featureId: n for n in self.nodes}
        self.spansByFeatureId = {s.featureId: s for s in self.spans}

        self.nodesByNodeId = {n.id: n for n in self.nodes}
        self.spansBySpanId = {s.id: s for s in self.spans}

        self.nodesSpacialIndex = QgsSpatialIndex(self.nodesLayer.getFeatures())
        self.spansSpacialIndex = QgsSpatialIndex(self.spansLayer.getFeatures())
