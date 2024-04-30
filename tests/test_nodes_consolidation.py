from qgis.core import QgsVectorLayer

from tool.model.comparison import (
    ConsolidationReason,
    NodeComparisonOutcome,
)
from tool.model.consolidation import NetworkNodesConsolidator
from tool.model.network import Network

import pytest


@pytest.mark.qgis_new_project()
def test_nodes_consolidation():
    a_nodes_layer = QgsVectorLayer("test_data/nodes_a.geojson", "a_nodes")
    a_spans_layer = QgsVectorLayer("test_data/spans_a.geojson", "a_spans")
    b_nodes_layer = QgsVectorLayer("test_data/nodes_b.geojson", "b_nodes")
    b_spans_layer = QgsVectorLayer("test_data/spans_b.geojson", "b_spans")

    network_a = Network.from_qgs_vectorlayers(a_nodes_layer, a_spans_layer)
    network_b = Network.from_qgs_vectorlayers(b_nodes_layer, b_spans_layer)

    nnc = NetworkNodesConsolidator(
        network_a, network_b, merge_above=100, ask_above=0, match_radius_km=10
    )

    comparisons = nnc.get_comparisons_to_ask_user()

    # Mock the user pressing Same on all comparisons
    comparisons_outcomes = [
        (
            comparison,
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
            ),
        )
        for comparison in comparisons
    ]

    nnc.finalise_with_user_comparison_outcomes(comparisons_outcomes)

    (consolidated_net_a, consolidated_net_b) = (
        nnc.get_networks_with_consolidated_nodes()
    )

    # Numbers based on the test data layers
    assert len(network_a.nodes) == 4
    assert len(network_b.nodes) == 4
    assert len(consolidated_net_a.nodes) == 5
    assert len(consolidated_net_b.nodes) == 5
