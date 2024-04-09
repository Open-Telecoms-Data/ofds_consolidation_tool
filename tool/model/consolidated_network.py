import json
from dataclasses import dataclass, asdict
from typing import List
from .network import Network, Node
from .comparison import NodeComparison


@dataclass(frozen=True)
class ConsolidationReason:
    """
    When two features are merged, this represents the relevant metadata.
    ie. ids of the two features, the confidence score, and a list of the
    properties with high similarity as the rationale.
    """

    feature_type: str
    primary_id: str
    secondary_id: str
    confidence: float
    matching_properties: list[str]
    manual: bool = False


class ConsolidatedNetwork(Network):

    network_a: Network
    network_b: Network

    merge_threshold: int
    ask_threshold: int

    nodes: List[Node]
    # spans: List[Span]
    node_comparisons: List[NodeComparison]
    # span_comparisons: List[SpanComparison]
    provenance: List[ConsolidationReason]

    def __init__(self, network_a, network_b, merge_above=100, ask_above=0):
        self.network_a = network_a
        self.network_b = network_b
        self.merge_threshold = merge_above
        self.ask_threshold = ask_above
        self.nodes = []
        self.node_comparisons = []
        self.provenance = []

        self.compare_nodes()
        self.update_spans()
        self.compare_spans()

    def compare_nodes(self):
        # TODO - this compares every node with every other node
        # - needs replacing with code to only compare to nearest neighbours instead
        for a_node in self.network_a.nodes:
            for b_node in self.network_b.nodes:
                comparison = NodeComparison(a_node, b_node)
                self.node_comparisons.append(comparison)
                if (
                    a_node.id == b_node.id
                ):  # TMP for testing - replace this with score threshold, ie:
                    # if comparison.confidence >= self.merge_threshold:
                    # TODO: ask user above ask_threshold
                    # duplicate found: keep primary (a)
                    #   todo: get user pref for which network to keep
                    #   todo: ability to merge rather than replace? (stretch goal)
                    matching_properties = comparison.get_high_scoring_properties()
                    reason = ConsolidationReason(
                        feature_type="NODE",
                        primary_id=a_node.id,
                        secondary_id=b_node.id,
                        confidence=comparison.confidence,
                        matching_properties=matching_properties,
                        manual=False,
                    )
                    self.provenance.append(reason)
                    if a_node not in self.nodes:
                        self.nodes.append(a_node)
                else:
                    # no match: keep both
                    if a_node not in self.nodes:
                        self.nodes.append(a_node)
                    if b_node not in self.nodes:
                        self.nodes.append(b_node)

    def update_spans(self):
        # TODO
        # after node comparision has been done, look through the start/ends of
        # spans and update any where duplicates were found and replaced
        pass

    def compare_spans(self):
        # TODO
        pass

    def count_comparisons(self):
        return len(self.node_comparisons)

    def count_merged(self):
        return len(self.provenance)

    def geojson(self, provenance=True):
        geo = {"type": "FeatureCollection", "features": []}

        for node in self.nodes:
            feat = {
                "type": "Feature",
                "geometry": node.geometry,
                "properties": node.properties,
            }
            if provenance:
                provenance = next(
                    (item for item in self.provenance if item.primary_id == node.id),
                    None,
                )
                if provenance:
                    feat["provenance"] = asdict(provenance)

            geo["features"].append(feat)

        return json.dumps(geo)
