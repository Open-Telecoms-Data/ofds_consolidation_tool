from enum import Enum
from typing import List, Optional, cast

import logging

from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QDialog
from qgis.core import (
    QgsMapLayer,
    QgsMapLayerType,
    QgsVectorLayer,
    QgsRasterLayer,
    QgsProject,
    QgsCoordinateReferenceSystem,
)

from .comparisons import FindNearestNodeComparison
from .gui import Ui_OFDSDedupToolDialog
from .models import Network, Node
from .helpers import isQgsMapLayerOFDS, MapController

logger = logging.getLogger(__name__)


class ToolUIState(str, Enum):
    READY_FOR_SELECTION = "READY_FOR_SELECTION"
    CONSOLIDATING_NODES = "CONSOLIDATING_NODES"
    CONSOLIDATING_SPANS = "CONSOLIDATING_SPANS"
    COMPLETE = "COMPLETE"


class OFDSDedupToolDialog(QDialog):
    ui: Ui_OFDSDedupToolDialog
    _ui_state: ToolUIState
    _osm_layer: Optional[QgsRasterLayer]
    _project: QgsProject

    # Display our data on the embedded maps in the Web Mercator CRS (aka EPSG 3857), as used by OpenStreetMap.
    # https://epsg.io/3857
    EPSG3857 = QgsCoordinateReferenceSystem("EPSG:3857")
    EPSG4328 = QgsCoordinateReferenceSystem("EPSG:4326")
    DISPLAY_CRS = EPSG3857

    def __init__(self):
        super().__init__()

        self.ui = Ui_OFDSDedupToolDialog()
        self.ui.setupUi(self)
        self.ui.startButton.clicked.connect(self.onNetworksSelected)

        self._osm_layer = None

        # Set initial UI state
        self._ui_state = ToolUIState.READY_FOR_SELECTION
        self.setUiState(self._ui_state)

    def _setUiSelectionEnabled(self, enabled: bool):
        """
        Enable/Disable all the layer selection drop-down boxes.
        We don't want the user to change layers in the middle of the process!
        """
        self.ui.nodesComboBoxA.setEnabled(enabled)
        self.ui.nodesComboBoxB.setEnabled(enabled)
        self.ui.spansComboBoxA.setEnabled(enabled)
        self.ui.spansComboBoxB.setEnabled(enabled)
        self.ui.startButton.setEnabled(enabled)

    def setUiState(self, state: ToolUIState):
        """
        Changes the tool UI from one state to another, enabling/disabling UI elements as needed.
        """
        logger.info(f"Changing State {self._ui_state} -> {state}")
        self._ui_state = state
        self._setUiSelectionEnabled(self._ui_state == ToolUIState.READY_FOR_SELECTION)

    @property
    def osmLayer(self) -> QgsRasterLayer:
        """
        Get the OpenStreetMap layer, creating it if necessary.
        """
        # TODO: Tidy up OSM layer when we're done with it, i.e. remove it from the project and set this cache to none when the user closes the UI
        if not self._osm_layer:
            osm_layer = QgsRasterLayer(
                "type=xyz&url=https://tile.openstreetmap.org/{z}/{x}/{y}.png&zmax=19&zmin=0&http-header:referer=",
                "OpenStreetMap",
                "wms",
            )

            if not osm_layer.isValid():
                logger.error("Failed to load OSM layer")
            else:
                self._project.addMapLayer(
                    osm_layer, False
                )  # False to prevent adding it to the legend

            # OpenStreetMap is EPSG 3857
            osm_layer.setCrs(self.EPSG3857)

            self._osm_layer = osm_layer

        return self._osm_layer

    def onNetworksSelected(self):
        # TODO: do some kind of check that the selected layers are OFDS?
        # Start by consolidating nodes

        self.networkA = Network(
            nodesLayer=self.ui.nodesComboBoxA.currentData(),
            spansLayer=self.ui.spansComboBoxA.currentData(),
        )

        self.networkB = Network(
            nodesLayer=self.ui.nodesComboBoxB.currentData(),
            spansLayer=self.ui.spansComboBoxB.currentData(),
        )

        self.setUiState(ToolUIState.CONSOLIDATING_NODES)

        # * setup the canvases
        self.mapA = MapController(
            mapCanvas=self.ui.mapA,
            network=self.networkA,
            project=self._project,
            osmLayer=self.osmLayer,
            displayCrs=self.DISPLAY_CRS,
        )

        self.mapB = MapController(
            mapCanvas=self.ui.mapB,
            network=self.networkB,
            project=self._project,
            osmLayer=self.osmLayer,
            displayCrs=self.DISPLAY_CRS,
        )

        self.mapA.zoomToEverything()
        self.mapB.zoomToEverything()

        self.nodeComparisonPairs = FindNearestNodeComparison(
            self.networkA, self.networkB
        ).findPotentialSameNodes()

        self.compareNodes(*self.nodeComparisonPairs.pop())

    def compareNodes(self, a: Node, b: Node):
        logger.info(f"Comparing Nodes {a} <-> {b}")
        self.mapA.zoomToNodeId(a.featureId)
        self.mapB.zoomToNodeId(b.featureId)

    def populateSelectionDropdowns(self, project: QgsProject):
        # Find all the layers the user has loaded
        layers: List[QgsMapLayer] = self._project.mapLayers(validOnly=True).values()

        # Populate the drop-down boxes (aka ComboBox) with the layers loaded into the project
        for combo_box in [
            self.ui.nodesComboBoxA,
            self.ui.spansComboBoxA,
            self.ui.nodesComboBoxB,
            self.ui.spansComboBoxB,
        ]:
            combo_box.clear()
            for layer in layers:
                # only vector layers can be valid OFDS layers
                # TODO: test that each layer is a OFDS layer first? maybe display all but disable non-OFDS layers?
                if layer.type() == QgsMapLayerType.VectorLayer and isQgsMapLayerOFDS(
                    cast(QgsVectorLayer, layer)
                ):
                    combo_box.addItem(layer.name(), layer)

    def reset(self, project: QgsProject):
        """
        Resets the tool to be ready to consolidate a new pair of networks.
        """
        self._project = project
        self.populateSelectionDropdowns(project)


class Worker(QThread):
    """Background thread for processing data without freezing the UI."""

    # TODO: todo
    pass
