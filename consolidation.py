from typing import List, Tuple

from qgis.core import QgsProject, QgsVectorLayer

from .comparisons import NodeComparison
from .models import FeatureComparisonOutcome, Network


def createNewNetworksWithConsolidatedNodes(
    project: QgsProject,
    networkA: Network,
    networkB: Network,
    nodeComparisonsOutcomes: List[Tuple[NodeComparison, FeatureComparisonOutcome]],
) -> Tuple[Network, Network]:
    consolidatedNodesLayer = QgsVectorLayer(
        "Point?crs=EPSG:4326", "_ofds_consolidation_temp_nodes", "memory"
    )
    # TODO: add a preference for A or B in FeatureComparisonOutcome

    consolidatedNodesLayer.startEditing()
    nodeLayerData = consolidatedNodesLayer.dataProvider()
    assert nodeLayerData is not None

    # TODO: Update span end/start data
    for nc, fco in nodeComparisonsOutcomes:
        if fco.areDuplicate:
            feature = nodeLayerData.addFeature(nc.features[0].feature)
        else:
            # TODO: Handle duplicate IDs across networks?
            nodeLayerData.addFeature(nc.features[0].feature)
            nodeLayerData.addFeature(nc.features[1].feature)

    consolidatedNodesLayer.commitChanges()

    newNetworkA = Network(
        nodesLayer=consolidatedNodesLayer, spansLayer=networkA.spansLayer
    )
    newNetworkB = Network(
        nodesLayer=consolidatedNodesLayer, spansLayer=networkB.spansLayer
    )

    return (newNetworkA, newNetworkB)
