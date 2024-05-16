from abc import ABC, abstractmethod
import json

from enum import Enum
from typing import Any, Dict, List, TypeVar, cast

from PyQt5.QtCore import QVariant

from qgis.core import (
    QgsFeature,
    QgsSpatialIndex,
    QgsVectorLayer,
    QgsWkbTypes,
    QgsField,
    QgsFields,
    QgsGeometry,
)


NESTED_PROPERTIES = [
    "end",
    "internationalConnections",
    "location",
    "network",
    "networkProviders",
    "phase",
    "physicalInfrastructureProvider",
    "start",
    "supplier",
]


class OFDSInvalidFeature(Exception):
    pass


class FeatureType(str, Enum):
    NODE = "NODE"
    SPAN = "SPAN"


class Feature(ABC):
    """
    A Node or Span.
    Wrapper around an OFDS-compliant QgsFeature.
    """

    featureId: int  # featureId is the QGIS-internal Id
    featureType: FeatureType
    featureGeometry: QgsGeometry
    id: str  # id is the OFDS id
    properties: Dict[str, Any]

    @abstractmethod
    def get(self, k: str) -> Any: ...

    @classmethod
    def from_qgis_feature(cls, feature: QgsFeature):
        attributes = feature.attributeMap()

        # Check if nested objects have been loaded by QGIS, and load them if not.
        properties = {}
        for attribute in attributes.keys():
            if attribute in NESTED_PROPERTIES and isinstance(
                attributes.get(attribute), str
            ):
                properties[attribute] = json.loads(attributes.get(attribute))
            else:
                properties[attribute] = attributes.get(attribute)

        if "id" not in properties or not isinstance(properties["id"], str):
            raise OFDSInvalidFeature
        ofds_id = properties["id"]
        return cls(
            id=ofds_id,
            properties=properties,
            featureId=feature.id(),
            featureGeometry=feature.geometry(),
        )

    def __init__(
        self,
        id: str,
        properties: Dict[str, Any],
        featureId: int,
        featureGeometry: QgsGeometry,
    ):
        self.id = id
        self.properties = self._convert_properties(properties)
        self.featureId = featureId
        self.featureGeometry = featureGeometry

        if (
            self.featureType == FeatureType.NODE
            and not self.featureGeometry.type()
            == QgsWkbTypes.GeometryType.PointGeometry
        ):
            raise OFDSInvalidFeature("Nodes layer must be PointGeometry")

        if (
            self.featureType == FeatureType.SPAN
            and not self.featureGeometry.type() == QgsWkbTypes.GeometryType.LineGeometry
        ):
            raise OFDSInvalidFeature("Spans layer must be LineGeometry")

    @property
    def name(self) -> str:
        """Human readable name"""
        return cast(str, self.properties.get("name", self.id))

    def with_new_id(self, new_id: str):
        # TODO: Update provenance somehow to reflect the ID change?
        props = self.properties.copy()
        props["id"] = new_id
        return self.__class__(
            new_id,
            properties=props,
            featureId=self.featureId,
            featureGeometry=self.featureGeometry,
        )

    def _convert_properties(self, properties):
        """Convert properties to their proper types. Node/Span specific."""
        return properties

    def __hash__(self) -> int:
        # Enable Nodes/Spans to be put in a Set or Dict
        # TODO: also add Network id when we get that
        return hash((self.id, self.featureId, self.featureType))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Feature):
            # TODO: also add Network id when we get that
            return (
                self.id == other.id
                and self.featureId == other.featureId
                and self.featureType == other.featureType
            )
        else:
            raise ValueError("Can't compare Feature to non-Feature")


class Node(Feature):
    featureType = FeatureType.NODE

    @classmethod
    def get_qgs_fields(cls) -> QgsFields:
        # Node fields according to schema:
        # https://open-fibre-data-standard.readthedocs.io/en/0.3/reference/schema.html#node
        fields = [
            QgsField(name="id", type=QVariant.Type.String),
            QgsField(name="featureType", type=QVariant.Type.String),
            QgsField(name="name", type=QVariant.Type.String),
            QgsField(name="phase", type=QVariant.Type.Map),
            QgsField(name="status", type=QVariant.Type.String),
            QgsField(name="address", type=QVariant.Type.Map),
            QgsField(name="type", type=QVariant.Type.StringList),
            QgsField(name="accessPoint", type=QVariant.Type.Bool),
            QgsField(
                name="internationalConnections",
                type=QVariant.Type.List,
                subType=QVariant.Type.Map,
            ),
            QgsField(name="power", type=QVariant.Type.Bool),
            QgsField(name="technologies", type=QVariant.Type.StringList),
            QgsField(name="physicalInfrastructureProvider", type=QVariant.Type.Map),
            QgsField(
                name="networkProviders",
                type=QVariant.Type.List,
                subType=QVariant.Type.Map,
            ),
            QgsField(name="network", type=QVariant.Type.Map),
            # provenance is non-standard field added by this tool
            QgsField(name="provenance", type=QVariant.Type.Map),
        ]

        qgs_fields = QgsFields()
        for field in fields:
            qgs_fields.append(field)

        return qgs_fields

    def _convert_properties(self, properties):
        return super()._convert_properties(properties)

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
            return self.featureGeometry.asPoint().toString()

        if k == "phase/name":
            phase = self.properties.get("phase", {})
            return phase.get("name")

        if k == "physicalInfrastructureProvider":
            # Only compare name, id is irrelevant
            pip = self.properties.get("physicalInfrastructureProvider", {})
            return pip.get("name")

        if k == "networkProviders":
            # Return a list of the names in the array, as other properties are irrelevant
            nps = self.properties.get("networkProviders", [])
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

    def __str__(self):
        return f"<Node {self.name}>"

    def __repr__(self):
        return f"<Node name={self.name}>"


class Span(Feature):
    featureType = FeatureType.SPAN

    @classmethod
    def get_qgs_fields(cls) -> QgsFields:
        # Span fields according to schema:
        # https://open-fibre-data-standard.readthedocs.io/en/0.3/reference/schema.html#span
        fields = [
            QgsField(name="id", type=QVariant.Type.String),
            QgsField(name="featureType", type=QVariant.Type.String),
            QgsField(name="name", type=QVariant.Type.String),
            QgsField(name="phase", type=QVariant.Type.Map),
            QgsField(name="status", type=QVariant.Type.String),
            QgsField(name="readyForServiceDate", type=QVariant.Type.String),
            QgsField(name="start", type=QVariant.Type.Map),
            QgsField(name="end", type=QVariant.Type.Map),
            QgsField(name="directed", type=QVariant.Type.Bool),
            QgsField(name="physicalInfrastructureProvider", type=QVariant.Type.Map),
            QgsField(
                name="networkProviders",
                type=QVariant.Type.List,
                subType=QVariant.Type.Map,
            ),
            QgsField(name="supplier", type=QVariant.Type.Map),
            QgsField(name="transmissionMedium", type=QVariant.Type.StringList),
            QgsField(name="deployment", type=QVariant.Type.StringList),
            QgsField(name="deploymentDetails", type=QVariant.Type.Map),
            QgsField(name="darkFibre", type=QVariant.Type.Bool),
            QgsField(name="fibreType", type=QVariant.Type.String),
            QgsField(name="fibreTypeDetails", type=QVariant.Type.Map),
            QgsField(name="fibreCount", type=QVariant.Type.Int),
            QgsField(name="fibreLength", type=QVariant.Type.Double),
            QgsField(name="technologies", type=QVariant.Type.StringList),
            QgsField(name="capacity", type=QVariant.Type.Double),
            QgsField(name="capacityDetails", type=QVariant.Type.Map),
            QgsField(name="countries", type=QVariant.Type.StringList),
            QgsField(name="network", type=QVariant.Type.Map),
            # provenance is non-standard field added by this tool
            QgsField(name="provenance", type=QVariant.Type.Map),
        ]

        qgs_fields = QgsFields()
        for field in fields:
            qgs_fields.append(field)

        return qgs_fields

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
            return {"id": start_id, "coordinates": start_location}

        if k == "end":
            # Return only id and coordinates
            end = self.properties.get("end", {})
            end_id = end.get("id")
            end_location = end.get("location", {}).get("coordinates")
            return {"id": end_id, "coordinates": end_location}

        if k == "phase/name":
            phase = self.properties.get("phase", {})
            return phase.get("name")

        if k == "physicalInfrastructureProvider":
            # Only compare name, id is irrelevant
            pip = self.properties.get("physicalInfrastructureProvider", {})
            return pip.get("name")

        if k == "networkProviders":
            # Return a list of the names in the array, as other properties are irrelevant
            nps = self.properties.get("networkProviders", [])
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
        return f"<Span {self.name}>"

    def __repr__(self) -> str:
        return f"<Span {self.name}>"


FeatureT = TypeVar("FeatureT", bound=Feature)


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
        nodes = list(Node.from_qgis_feature(f) for f in list(nodesLayer.getFeatures()))
        spans = list(Span.from_qgis_feature(f) for f in list(spansLayer.getFeatures()))

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
