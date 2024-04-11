import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from qgis.core import QgsPointXY, QgsWkbTypes, QgsDistanceArea
from .network import Node, Span

from ..._lib.jellyfish import _jellyfish as jellyfish

logger = logging.getLogger(__name__)


ALL_NODE_PROPERTIES = [
    "name",
    "phase/name",
    "physicalInfrastructureProvider",
    "accessPoint",
    "power",
    "status",
    "location/coordinates",
    "location/address/streetAddress",
    "location/address/locality",
    "location/address/region",
    "location/address/postalCode",
    "location/address/country",
    "type",
    "internationalConnections/streetAddress",
    "internationalConnections/region",
    "internationalConnections/postalCode",
    "internationalConnections/country",
    "networkProviders",
]


class Comparison:
    """
    Generalised comparision class for things that are common between Node and
    Span comparisons.
    """

    total: float
    weights: dict
    scores: dict
    confidence: float

    def __init__(self, weights=None):
        self.weights = weights if weights else self.default_weights()

    def default_weights(self) -> Dict[str, float]:
        # We can pass different weights in for nodes and spans, but falls back to this.
        weights = {
            "name": 0.5,
            "phase/name": 0.75,
            "physicalInfrastructureProvider": 0.75,
            "accessPoint": 0.6,
            "power": 0.5,
            "status": 0.2,
            "location/coordinates": 1,
            "location/address/streetAddress": 0.9,
            "location/address/locality": 0.75,
            "location/address/region": 0.1,
            "location/address/postalCode": 0.8,
            "location/address/country": 0.1,
            "type": 0.75,
            "internationalConnections/streetAddress": 0.1,
            "internationalConnections/region": 0.1,
            "internationalConnections/postalCode": 0.1,
            "internationalConnections/country": 0.2,
            "networkProviders": 0.75,
        }
        return weights

    def weight(self, prop):
        return self.weights.get(prop)

    def calculate_total(self):
        # calculate total from scores*weights
        total = 0
        for k, v in self.scores.items():
            total += v * self.weight(k)
        self.total = total

    def calculate_confidence(self):
        # Turn the total into a %
        highest = sum(self.weights.values())
        self.confidence = self.total / highest * 100

    def get_high_scoring_properties(self):
        return [k for k, v in self.scores.items() if v > 0.5]

    def compare_equals(self, first, second):
        if first == second:
            return 1
        else:
            return 0

    def compare_strings(self, first, second):
        if first is None or second is None:
            return 0
        return jellyfish.jaro_winkler_similarity(first, second)

    def compare_array_codelist(self, first, second):
        first.sort()
        second.sort()
        return 1 if first == second else 0

    def compare_types(self, first, second):
        # TODO: this might be more complex as the value is a union of types from all
        #       network providers.
        # So we may need a more nuanced approach to comparison in case one dataset is
        # missing a provider
        return self.compare_array_codelist(first, second)

    def compare_networkProviders(self, first, second):
        first.sort()
        second.sort()
        # TODO
        # if functools.reduce(
        #       lambda x, y : x and y, map(
        #           lambda p, q: p == q,
        #           first_names,
        #           second_names
        #       ),
        #       True
        #   ):
        # I want to do a string comparision on the names in case of typos,
        # but not sure if it's worth comparing everything in one list with everything
        # in the other list.
        pass

    def compare_internationalConnections(self, first, second):
        # TODO
        # Decide how to handle this array of objects, several fields are relevant
        pass


@dataclass
class NodeComparison(Comparison):
    node_a: Node
    node_b: Node
    total: float
    confidence: float
    scores: Dict[str, float]
    weight: Dict[str, float]

    def __init__(
        self,
        node_a: Node,
        node_b: Node,
        weights: Optional[Dict[str, float]] = None,
    ):
        self.features = (node_a, node_b)
        self.node_a = node_a
        self.node_b = node_b
        self.weights = weights if weights else self.default_weights()

        # TODO: currently this will score low if one is missing - what we actually need
        #       is not to score it at all
        # TODO: we get a strong match if both are missing - should not be counted
        self.scores = {
            "name": self.compare_strings(node_a.get("name"), node_b.get("name")),
            "type": self.compare_types(node_a.get("type"), node_b.get("type")),
            "location/address/country": self.compare_equals(
                node_a.get("location/address/country"),
                node_b.get("location/address/country"),
            ),
            "location/address/streetAddress": self.compare_strings(
                node_a.get("location/address/streetAddress"),
                node_b.get("location/address/streetAddress"),
            ),
            "location/address/postalCode": self.compare_strings(
                node_a.get("location/address/postalCode"),
                node_b.get("location/address/postalCode"),
            ),
            "location/address/region": self.compare_strings(
                node_a.get("location/address/region"),
                node_b.get("location/address/region"),
            ),
            "location/address/locality": self.compare_strings(
                node_a.get("location/address/locality"),
                node_b.get("location/address/locality"),
            ),
            "phase/name": self.compare_strings(
                node_a.get("phase/name"), node_b.get("phase/name")
            ),
            "status": self.compare_equals(node_a.get("status"), node_b.get("status")),
            "power": self.compare_equals(node_a.get("power"), node_b.get("power")),
            "accessPoint": self.compare_equals(
                node_a.get("accessPoint"), node_b.get("accessPoint")
            ),
            "physicalInfrastructureProvider": self.compare_strings(
                node_a.get("physicalInfrastructureProvider"),
                node_b.get("physicalInfrastructureProvider"),
            ),
        }

        logger.debug(self.scores)

        self.calculate_total()
        self.calculate_confidence()

    @classmethod
    def _point_distance_km(self, point_a: QgsPointXY, point_b: QgsPointXY) -> float:
        """Calculate the distance between two points, in kilometers."""
        calc = QgsDistanceArea()
        calc.setEllipsoid("WGS84")

        dist_meters = calc.measureLine(point_a, point_b)

        return dist_meters / 1000.0

    @property
    def distance_km(self):
        assert (
            self.node_a.feature.geometry().wkbType()
            == QgsWkbTypes.GeometryType.PointGeometry
        )
        assert (
            self.node_b.feature.geometry().wkbType()
            == QgsWkbTypes.GeometryType.PointGeometry
        )

        point_a = self.node_a.feature.geometry().asPoint()
        point_b = self.node_b.feature.geometry().asPoint()

        return self._point_distance_km(point_a, point_b)


@dataclass
class SpanComparison(Comparison):
    features: Tuple[Span, Span]
    node_a_id: str
    node_b_id: str
    total: float
    confidence: float
    scores: dict

    def __init__(self, span_a, span_b, weights=None):
        self.features = (span_a, span_b)
        self.span_a_id = span_a.id
        self.span_b_id = span_b.id
        self.weights = weights if weights else self.default_weights()

        self.scores = {}  # TODO

        self.calculate_total()
        self.calculate_confidence()

    def compare_line_proximity(self, first, second):
        # TODO
        # Return a higher score the closer together two lines are.
        # This might not be very accurate, so think about how much to depend on it.
        # Compare only if they're given to a certain degree of accuracy in the
        # coordinates?
        # or calculate score based on accuracy as well as proximity
        # Thresholds tbd
        pass

    def compare_start_and_end_nodes(self, first, second):
        # TODO
        # Doesn't matter which is start and which is end
        # Compare based on id, after node consolidation has happened
        # Return 1 if both pairs are the same, 0.2(?) if one is the same, 0 if neither
        # tbd: worth the effort of comparing proximity of start and end nodes if they're
        # not an exact match?
        pass


@dataclass(frozen=True)
class ComparisonOutcome:
    """
    Represents the outcome of the comparison of two features by the user.
    """

    consolidate: bool
