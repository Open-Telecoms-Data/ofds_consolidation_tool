import logging
from pathlib import Path
from qgis.core import QgsVectorLayer

from tool.model.comparison import (
    ConsolidationReason,
    NodeComparisonOutcome,
)
from tool.model.consolidation import NetworkNodesConsolidator
from tool.model.network import Network

# QgsApplication.setPrefixPath("/usr")  # for Linux?

from .. import setup_logging

logger = logging.getLogger(__name__)

setup_logging()


def test_nodes_consolidation(qgis_app, qgis_new_project, request):

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

    network_a = Network.from_qgs_vectorlayers(a_nodes_layer, a_spans_layer)
    network_b = Network.from_qgs_vectorlayers(b_nodes_layer, b_spans_layer)

    # Numbers based on the test data layers
    assert len(network_a.nodes) == 4
    assert len(network_b.nodes) == 4

    nnc = NetworkNodesConsolidator(
        network_a, network_b, merge_above=100, ask_above=0, match_radius_km=10
    )

    comparisons = nnc.get_comparisons_to_ask_user()

    logger.info(f"{len(comparisons)=}")

    # Mock the user pressing Same on all comparisons
    comparison_outcomes = [
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
        for comparison in comparisons
    ]

    nnc.add_comparison_outcomes(comparison_outcomes)

    (consolidated_net_a, consolidated_net_b) = (
        nnc.get_networks_with_consolidated_nodes()
    )

    # Numbers based on the test data layers
    assert len(consolidated_net_a.nodes) == 5
    assert len(consolidated_net_b.nodes) == 5
