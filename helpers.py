from qgis.core import (
    QgsVectorLayer,
    QgsProject,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsMapLayer,
)
from qgis.gui import QgsMapCanvas

from .models import Network


def isQgsMapLayerOFDS(layer: QgsVectorLayer) -> bool:
    """
    Try to figure out if a given layer is OFDS or not, so we can warn users if they try to use a non-OFDS layer with the consolidation tool.
    """
    # TODO: how?
    return True


class MapController:
    """
    Helper class to wrap around a QgsMapCanvas and a VectorLayer, to make setup and control easier.
    """

    def __init__(
        self,
        mapCanvas: QgsMapCanvas,
        network: Network,
        project: QgsProject,
        osmLayer: QgsMapLayer,
        displayCrs: QgsCoordinateReferenceSystem,
    ):
        self.mapCanvas = mapCanvas
        self.network = network
        self.nodesLayer = network.nodesLayer
        self.spansLayer = network.spansLayer
        self.osmLayer = osmLayer
        self.displayCrs = displayCrs
        self.transform = QgsCoordinateTransform(
            self.nodesLayer.crs(), displayCrs, project
        )

        self._reset()

    def _reset(self):
        self.mapCanvas.enableAntiAliasing(True)
        self.mapCanvas.setDestinationCrs(self.displayCrs)
        self.mapCanvas.setLayers([self.nodesLayer, self.spansLayer, self.osmLayer])

    def zoomToNodeByFeatureId(self, nodeId):
        """
        Display the given node and surrounding area.
        """
        self.mapCanvas.zoomToFeatureIds(self.nodesLayer, [nodeId])
        # We need to "refresh" i.e. re-render the map after every time we make changes
        self.mapCanvas.refresh()

    def zoomToSpanByFeatureId(self, spanId):
        """
        Display the given span and surrounding area.
        """
        self.mapCanvas.zoomToFeatureIds(self.nodesLayer, [spanId])
        # We need to "refresh" i.e. re-render the map after every time we make changes
        self.mapCanvas.refresh()

    def zoomToEverything(self):
        """
        Display the whole layer at once. Probably not that useful, nice for testing maps though.
        """
        extentInSourceCrs = self.nodesLayer.extent()
        extentInDisplayCrs = self.transform.transformBoundingBox(extentInSourceCrs)
        self.mapCanvas.zoomToFeatureExtent(extentInDisplayCrs)
        # We need to "refresh" i.e. re-render the map after every time we make changes
        self.mapCanvas.refresh()
