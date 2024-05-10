import logging
from pathlib import Path
from typing import Tuple
from qgis.core import QgsVectorLayer

from tool.model.comparison import (
    ConsolidationReason,
    NodeComparisonOutcome,
    SpanComparisonOutcome,
)
from tool.model.consolidation import NetworkNodesConsolidator, NetworkSpansConsolidator
from tool.model.network import Network

# QgsApplication.setPrefixPath("/usr")  # for Linux?

from .. import setup_logging

logger = logging.getLogger(__name__)

setup_logging()


def load_test_networks(request) -> Tuple[Network, Network]:
    test_data_dir = Path(Path(request.path).parent, "test_data").absolute()

    a_nodes_uri = "GeoJSON:" + Path(test_data_dir, "nodes_a.geojson").as_posix()
    a_spans_uri = "GeoJSON:" + Path(test_data_dir, "spans_a.geojson").as_posix()
    b_nodes_uri = "GeoJSON:" + Path(test_data_dir, "nodes_b.geojson").as_posix()
    b_spans_uri = "GeoJSON:" + Path(test_data_dir, "spans_b.geojson").as_posix()

    logger.info(f"{a_nodes_uri=}")

    a_nodes_layer = QgsVectorLayer(a_nodes_uri, "a_nodes", "ogr")
    a_spans_layer = QgsVectorLayer(a_spans_uri, "a_spans", "ogr")
    b_nodes_layer = QgsVectorLayer(b_nodes_uri, "b_nodes", "ogr")
    b_spans_layer = QgsVectorLayer(b_spans_uri, "b_spans", "ogr")

    # Numbers based on the test data layers
    assert len(list(a_nodes_layer.getFeatures())) == 4
    assert len(list(b_nodes_layer.getFeatures())) == 4
    assert len(list(a_spans_layer.getFeatures())) == 3
    assert len(list(b_spans_layer.getFeatures())) == 3

    network_a = Network.from_qgs_vectorlayers(a_nodes_layer, a_spans_layer)
    network_b = Network.from_qgs_vectorlayers(b_nodes_layer, b_spans_layer)

    # Numbers based on the test data layers
    assert len(network_a.nodes) == 4
    assert len(network_b.nodes) == 4
    assert len(network_a.spans) == 3
    assert len(network_b.spans) == 3

    return (network_a, network_b)


def test_consolidation(qgis_app, qgis_new_project, request):
    network_a, network_b = load_test_networks(request)

    # Test Nodes Consolidation
    nnc = NetworkNodesConsolidator(
        network_a, network_b, merge_above=100, ask_above=0, match_radius_km=10
    )

    node_comparisons = nnc.get_comparisons_to_ask_user()

    logger.info(f"{len(node_comparisons)=}")

    # Mock the user pressing Same on all comparisons
    node_comparison_outcomes = [
        NodeComparisonOutcome(
            comparison=comparison,
            consolidate=ConsolidationReason(
                feature_type="NODE",
                primary=comparison.feature_a,
                secondary=comparison.feature_b,
                confidence=comparison.confidence,
                matching_properties=comparison.get_high_scoring_properties(),
                manual=True,
            ),
        )
        for comparison in node_comparisons
    ]

    nnc.add_comparison_outcomes(node_comparison_outcomes)

    (network_a_consolidated_nodes, network_b_consolidated_nodes) = (
        nnc.get_networks_with_consolidated_nodes()
    )

    # Numbers based on the test data layers
    assert len(network_a_consolidated_nodes.nodes) == 5
    assert len(network_b_consolidated_nodes.nodes) == 5

    # Test Spans Consolidation
    nsc = NetworkSpansConsolidator(
        network_a_consolidated_nodes, network_b_consolidated_nodes
    )

    span_comparisons = nsc.get_comparisons_to_ask_user()

    # Simulate pressing Same on all comparisons
    span_comparison_outcomes = [
        SpanComparisonOutcome(
            sc,
            ConsolidationReason(
                feature_type="SPAN",
                primary=sc.feature_a,
                secondary=sc.feature_b,
                confidence=sc.confidence,
                matching_properties=sc.get_high_scoring_properties(),
                manual=True,
            ),
        )
        for sc in span_comparisons
    ]

    consolidated_network = nsc.get_consolidated_network_with_user_comparison_outcomes(
        span_comparison_outcomes
    )

    # Numbers based on test data layers
    # Check that nodes haven't changed
    assert len(consolidated_network.nodes) == 5
    assert len(list(consolidated_network.nodesLayer.getFeatures())) == 5
    # Check for the expected number of Spans
    assert len(consolidated_network.spans) == 4
    assert len(list(consolidated_network.spansLayer.getFeatures())) == 4
