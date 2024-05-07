import logging
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Dict,
    Generic,
    List,
    Literal,
    Optional,
    Tuple,
    TypeVar,
    Union,
)
from qgis.core import QgsPointXY, QgsWkbTypes, QgsDistanceArea, QgsUnitTypes

from .network import Feature, Node, Span

from .._lib.jellyfish import _jellyfish as jellyfish

logger = logging.getLogger(__name__)


ALL_NODE_PROPERTIES = [
    "name",
    "phase/name",
    "physicalInfrastructureProvider",
    "accessPoint",
    "power",
    "status",
    "coordinates",
    "location/address/streetAddress",
    "location/address/locality",
    "location/address/region",
    "location/address/postalCode",
    "location/address/country",
    "type",
    "internationalConnections/streetAddress",
    "internationalConnections/region",
    "internationalConnections/locality",
    "internationalConnections/postalCode",
    "internationalConnections/country",
    "networkProviders",
]


ALL_SPAN_PROPERTIES = [
    "name",
    "phase/name",
    "readyForServiceDate",
    "start",
    "end",
    "physicalInfrastructureProvider",
    "coordinates",
    "networkProviders",
    "supplier",
    "transmissionMedium",
    "deployment",
    "fibreType",
    "fibreCount",
    "fibreLength",
    "capacity",
    "countries",
    "status",
]


class Comparison:
    """
    Generalised comparision class for things that are common between Node and
    Span comparisons.ro
    """

    features: Tuple[Feature, Feature]
    total: float
    weights: dict
    scores: dict
    confidence: float

    @property
    def feature_a(self):
        return self.features[0]

    @property
    def feature_b(self):
        return self.features[1]

    def __init__(self, weights=None):
        if weights:
            self.weights = weights
        else:
            self.weights = dict()

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
        # Return scores that are over 0.5 - this is arbitrary, may want to increase
        return [k for k, v in self.scores.items() if v > 0.5]

    def compare_equals(self, first, second):
        if first == second and first is not None:
            return 1
        return 0

    def compare_strings(self, first, second):
        if first is None or second is None:
            return 0
        return jellyfish.jaro_winkler_similarity(first, second)

    def compare_array_codelist_equals(self, first, second):
        """Score arrays 1 if they are identical, 0 if not."""
        list(first or []).sort()
        list(second or []).sort()
        return 1 if first == second and first != [] else 0

    def compare_array_codelist_matches(self, first, second):
        """Score arrays on a scale based on amount of overlap."""
        first = set(first or [])
        second = set(second or [])
        intersection = first & second
        difference = first ^ second
        union = first | second
        if self.compare_array_codelist_equals(first, second):
            # Full marks if they're identical
            return 1
        if len(intersection) == 0:
            # No marks if no overlap at all
            return 0
        # If more values the same than different, return a middling score
        if len(union) - len(difference) > 0:
            return 0.75
        # Else return a low score - still some overlap.
        # This is very crude, should refine after seeing more data.
        return 0.25

    def compare_array_strings(self, first, second):
        """
        Score arrays of free text strings based on string similarity.
        """
        if not first or not second:
            return 0
        scores = []
        for f in first:
            for s in second:
                score = self.compare_strings(f, s)
                # > 0.8 is a decent match but not using this fact anywhere.
                scores.append(score)
        # Return average scores over number of comparisons made
        return sum(scores) / (len(first) * len(second))

    def compare_types(self, first, second):
        return self.compare_array_codelist_matches(first, second)

    def compare_networkProviders(self, first, second):
        """Expects a list of names of network providers only."""
        if first == [] and second == []:
            return 0
        first = set(first)
        second = set(second)
        if self.compare_array_codelist_equals(first, second):
            # Full marks if they're identical
            return 1
        # Else do string comparision in case of typos.
        return self.compare_array_strings(first, second)


@dataclass
class NodeComparison(Comparison):
    features: Tuple[Node, Node]
    total: float
    confidence: float
    scores: Dict[str, float]
    weight: Dict[str, float]

    @property
    def node_a(self):
        return self.features[0]

    @property
    def node_b(self):
        return self.features[1]

    def __init__(
        self,
        node_a: Node,
        node_b: Node,
        weights: Optional[Dict[str, float]] = None,
    ):
        self.features = (node_a, node_b)
        self.weights = weights if weights else self.default_node_weights()

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
            "coordinates": self.compare_proximity(),
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
            "networkProviders": self.compare_networkProviders(
                node_a.get("networkProviders"),
                node_b.get("networkProviders"),
            ),
            "internationalConnections/streetAddress": self.compare_array_strings(
                node_a.get("internationalConnections/streetAddress"),
                node_b.get("internationalConnections/streetAddress"),
            ),
            "internationalConnections/region": self.compare_array_strings(
                node_a.get("internationalConnections/region"),
                node_b.get("internationalConnections/region"),
            ),
            "internationalConnections/locality": self.compare_array_strings(
                node_a.get("internationalConnections/locality"),
                node_b.get("internationalConnections/locality"),
            ),
            "internationalConnections/postalCode": self.compare_array_strings(
                node_a.get("internationalConnections/postalCode"),
                node_b.get("internationalConnections/postalCode"),
            ),
            "internationalConnections/country": self.compare_array_codelist_equals(
                node_a.get("internationalConnections/country"),
                node_b.get("internationalConnections/country"),
            ),
        }

        self.calculate_total()
        self.calculate_confidence()

    def default_node_weights(self) -> Dict[str, float]:
        # We can pass different weights on the fly if needed, but falls back to this.
        weights = {
            "name": 0.5,
            "phase/name": 0.75,
            "physicalInfrastructureProvider": 0.75,
            "accessPoint": 0.6,
            "power": 0.5,
            "status": 0.2,
            "coordinates": 1,
            "location/address/streetAddress": 0.9,
            "location/address/locality": 0.75,
            "location/address/region": 0.1,
            "location/address/postalCode": 0.8,
            "location/address/country": 0.1,
            "type": 0.75,
            "internationalConnections/streetAddress": 0.1,
            "internationalConnections/region": 0.1,
            "internationalConnections/locality": 0.1,
            "internationalConnections/postalCode": 0.1,
            "internationalConnections/country": 0.2,
            "networkProviders": 0.75,
        }
        return weights

    @classmethod
    def _point_distance_km(self, point_a: QgsPointXY, point_b: QgsPointXY) -> float:
        """Calculate the distance between two points, in kilometers."""
        calc = QgsDistanceArea()
        calc.setEllipsoid("WGS84")

        dist = calc.measureLine(point_a, point_b)
        dist_km = calc.convertLengthMeasurement(
            dist, QgsUnitTypes.DistanceUnit.DistanceKilometers
        )

        return dist_km

    @property
    def distance_km(self) -> float:
        assert self.node_a.featureGeometry.wkbType() == QgsWkbTypes.Type.Point
        assert self.node_b.featureGeometry.wkbType() == QgsWkbTypes.Type.Point

        point_a = self.node_a.featureGeometry.asPoint()
        point_b = self.node_b.featureGeometry.asPoint()

        return self._point_distance_km(point_a, point_b)

    def __eq__(self, value: object) -> bool:
        if isinstance(value, NodeComparison):
            return (self.node_a == value.node_a) and (self.node_b == value.node_b)
        else:
            raise ValueError("Can't test equality with non-NodeComparison")

    def compare_proximity(self):
        """Score based on distance between nodes."""
        min_to_score = 50  # We can fine tune if need be.
        return (
            0
            if self.distance_km > min_to_score
            else 1 - self.distance_km / min_to_score
        )


@dataclass
class SpanComparison(Comparison):
    features: Tuple[Span, Span]
    span_a_id: str
    span_b_id: str
    total: float
    confidence: float
    scores: dict

    @property
    def span_a(self):
        return self.features[0]

    @property
    def span_b(self):
        return self.features[1]

    def __init__(self, span_a, span_b, weights=None):
        self.features = (span_a, span_b)
        self.span_a_id = span_a.id
        self.span_b_id = span_b.id
        self.weights = weights if weights else self.default_span_weights()

        self.scores = {
            "name": self.compare_strings(span_a.get("name"), span_b.get("name")),
            "nodes": self.compare_start_and_end_nodes(
                [span_a.get("start"), span_a.get("end")],
                [span_b.get("start"), span_b.get("end")],
            ),
            "phase/name": self.compare_strings(
                span_a.get("phase/name"), span_b.get("phase/name")
            ),
            "status": self.compare_equals(span_a.get("status"), span_b.get("status")),
            "countries": self.compare_array_codelist_equals(
                span_a.get("countries"), span_b.get("countries")
            ),
            "physicalInfrastructureProvider": self.compare_strings(
                span_a.get("physicalInfrastructureProvider"),
                span_b.get("physicalInfrastructureProvider"),
            ),
            "networkProviders": self.compare_networkProviders(
                span_a.get("networkProviders"),
                span_b.get("networkProviders"),
            ),
            # TODO: check what actual format readyForServiceDate should be and if we
            #       should do proper date comparision
            # it's just a string in the standard
            "readyForServiceDate": self.compare_equals(
                span_a.get("readyForServiceDate"), span_b.get("readyForServiceDate")
            ),
            "transmissionMedium": self.compare_array_codelist_equals(
                span_a.get("transmissionMedium"), span_b.get("transmissionMedium")
            ),
            "deployment": self.compare_array_codelist_equals(
                span_a.get("deployment"), span_b.get("deployment")
            ),
            "supplier": self.compare_strings(
                span_a.get("supplier"), span_b.get("supplier")
            ),
            "fibreLength": self.compare_fibreLength(
                span_a.get("fibreLength"), span_b.get("fibreLegnth")
            ),
            "fibreCount": self.compare_equals(
                span_a.get("fibreCount"), span_b.get("fibreCount")
            ),  # TODO: check if this should be equals or if there's a threshold to use
            "fibreType": self.compare_equals(
                span_a.get("fibreType"), span_b.get("fibreType")
            ),
            "capacity": self.compare_equals(
                span_a.get("capacity"), span_b.get("capacity")
            ),  # TODO: check if this should be equals or if there's a threshold to use
        }

        self.calculate_total()
        self.calculate_confidence()

    def default_span_weights(self) -> Dict[str, float]:
        weights = {
            "name": 0.5,
            "phase/name": 0.75,
            "readyForServiceDate": 0.75,
            "nodes": 1,
            "physicalInfrastructureProvider": 0.75,
            "coordinates": 0.75,
            "supplier": 0.75,
            "transmissionMedium": 0.75,
            "deployment": 0.75,
            "fibreType": 0.75,
            "fibreCount": 0.75,
            "fibreLength": 0.75,
            "capacity": 0.75,
            "countries": 0.1,
            "status": 0.1,
            "networkProviders": 0.5,
        }
        return weights

    def _normalise_start_and_end_node_ids(self, start, end):
        """
        We're ignoring direction, so this puts the ids into a set so we can check
        for intersection.
        """
        return {start.get("id"), end.get("id")}

    def compare_fibreLength(self, first, second):
        """
        Score 0 if longer than 1km difference, otherwise the closer the length the
        higher the score. TODO: check the 1km threshold.
        """
        if first is None or second is None:
            return 0
        diff = abs(first - second)
        return 1 - diff if diff < 1 else 0

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
        """
        See if there are matches between the pair of nodes at the ends of the spans.
        Input is two lists, containing the start and end data for each span being compared.
        TODO: worth the effort of comparing proximity of start and end nodes if they're
        not an exact match?
        """
        nodes_a = self._normalise_start_and_end_node_ids(first[0], first[1])
        nodes_b = self._normalise_start_and_end_node_ids(second[0], second[1])
        overlap = len(nodes_a & nodes_b)
        if overlap == 2:  # they're the same
            return 1
        if (
            overlap == 1
        ):  # one end is the same, which probably isn't meaningful, but more than nothing
            return 0.2
        return 0


ComparisonT = TypeVar("ComparisonT", NodeComparison, SpanComparison)


@dataclass(frozen=True)
class ConsolidationReason:
    """
    When two features are merged, this represents the relevant metadata.
    ie. ids of the two features, the confidence score, and a list of the
    properties with high similarity as the rationale.
    """

    feature_type: str
    primary: Feature
    secondary: Feature
    confidence: float
    matching_properties: List[str]
    manual: bool = False


@dataclass(frozen=True)
class ComparisonOutcome(Generic[ComparisonT]):
    """
    Represents the outcome of the comparison of two Features by the user.
    """

    comparison: ComparisonT

    # Consolidate is either False, or an instance of ConsolidationReason
    consolidate: Union[Literal[False], ConsolidationReason]


if TYPE_CHECKING:
    NodeComparisonOutcome = ComparisonOutcome[NodeComparison]
    SpanComparisonOutcome = ComparisonOutcome[SpanComparison]
else:
    NodeComparisonOutcome = ComparisonOutcome
    SpanComparisonOutcome = ComparisonOutcome

# @dataclass(frozen=True)
# class NodeComparisonOutcome(ComparisonOutcome[NodeComparison]):
#    pass
#
#
# @dataclass(frozen=True)
# class SpanComparisonOutcome(ComparisonOutcome[SpanComparison]):
#    pass
