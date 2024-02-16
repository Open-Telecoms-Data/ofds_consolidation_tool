import logging
from typing import List, Optional, Tuple, Union
import json
from dataclasses import dataclass
from PyQt5.QtWidgets import QPlainTextEdit, QPushButton, QWidget, QComboBox
from qgis.core import QgsMapLayer, QgsVectorLayer, QgsProject, QgsCoordinateTransform
from qgis.gui import QgsMapCanvas

from ..gui import Ui_OFDSDedupToolDialog

from ..helpers import EPSG3857, getOpenStreetMapLayer
from ..models import FeatureComparisonOutcome, Node, Span, FeatureType
from .state import (
    ToolLayerSelectState,
    ToolNodeComparisonState,
    ToolSpanComparisonState,
    ToolState,
)

logger = logging.getLogger(__name__)


class InvalidViewState(Exception):
    pass


#
# Component Views
#

# All views should have an "update" method which accepts relevent parts of state and
# updates the relevents of the UI to reflect the state.


class MiniMapView:
    """
    Helper class to wrap around a QgsMapCanvas and a VectorLayer, to make setup and
    control easier.
    """

    # Display our data on the embedded maps in the Web Mercator CRS (aka EPSG 3857),
    # as used by OpenStreetMap.
    # https://epsg.io/3857
    DISPLAY_CRS = EPSG3857

    @dataclass(frozen=True)
    class State:
        """The state to pass to MiniMapView.update"""

        nodesLayer: QgsVectorLayer
        spansLayer: QgsVectorLayer
        featureId: int
        featureType: FeatureType

    @dataclass(frozen=True)
    class Layers:
        nodesLayer: QgsVectorLayer
        spansLayer: QgsVectorLayer

    # Attributes
    layers: Optional[Layers]
    backgroundLayer: QgsMapLayer

    def __init__(
        self,
        mapCanvas: QgsMapCanvas,
        backgroundLayer: QgsMapLayer,
    ):
        self.mapCanvas = mapCanvas
        self.backgroundLayer = backgroundLayer
        self.mapCanvas.enableAntiAliasing(True)
        self.mapCanvas.setDestinationCrs(self.DISPLAY_CRS)

    def _zoomToEverything(self):
        if not self.layers:
            raise InvalidViewState

        transform = QgsCoordinateTransform(
            self.layers.nodesLayer.crs(), self.DISPLAY_CRS, QgsProject.instance()
        )
        extentInSourceCrs = self.layers.nodesLayer.extent()
        extentInDisplayCrs = transform.transformBoundingBox(extentInSourceCrs)
        self.mapCanvas.zoomToFeatureExtent(extentInDisplayCrs)
        # We need to "refresh" i.e. re-render the map after every time we make changes
        self.mapCanvas.refresh()

    def update(self, state: Optional[State]):
        if state is None:
            # Nothing to display, so display nothing
            logger.info("RESET MAP")
            self.layers = None
            self.mapCanvas.setLayers([])
            self.mapCanvas.refresh()
            return

        # From this point on, we have state to display
        if self.layers is None:
            # We got new layers! Setup the map.
            self.layers = self.Layers(
                nodesLayer=state.nodesLayer, spansLayer=state.spansLayer
            )
            self.mapCanvas.setLayers(
                [self.layers.nodesLayer, self.layers.spansLayer, self.backgroundLayer]
            )
            logger.info(f"MiniMap has new {self.mapCanvas.layers()=}")
            self._zoomToEverything()

        # Check to make sure the layers haven't change for some reason
        if (
            state.nodesLayer != self.layers.nodesLayer
            or state.spansLayer != self.layers.spansLayer
        ):
            # We shouldn't get surprise layer changes
            raise InvalidViewState

        # Zoom the map to and hilight the relevent feature
        if state.featureType == FeatureType.NODE:
            self.mapCanvas.zoomToFeatureIds(self.layers.nodesLayer, [state.featureId])
            self.layers.nodesLayer.selectByIds([state.featureId])

        elif state.featureType == FeatureType.SPAN:
            self.mapCanvas.zoomToFeatureIds(self.layers.spansLayer, [state.featureId])
            self.layers.spansLayer.selectByIds([state.featureId])

        else:
            raise InvalidViewState

        # We need to "refresh" to rerender the map after changing it
        self.mapCanvas.refresh()


class InfoPanelView:
    infoPanel: QPlainTextEdit

    def __init__(self, infoPanel: QPlainTextEdit):
        self.infoPanel = infoPanel

    def update(self, feature: Union[Node, Span, None]):
        """
        Display the given Feature, or nothing.
        """
        if feature is None:
            # No feature to display, e.g. still selecting layers
            self.infoPanel.setPlainText("")
            self.infoPanel.setEnabled(False)

        else:
            # Display feature info
            self.infoPanel.setEnabled(True)
            if isinstance(feature, Node):
                # Display Node info
                # TODO: make prettier. Maybe use non-plaintext
                self.infoPanel.setPlainText(json.dumps(feature.data, indent=2))

            elif isinstance(feature, Span):
                # Display Span info
                # TODO: make prettier. Maybe use non-plaintext
                self.infoPanel.setPlainText(json.dumps(feature.data, indent=2))

            else:
                raise InvalidViewState


#
# Section-level views
#


class LayerSelectView:
    """
    The view which renders the layer selection part of the UI.
    """

    nodesComboBoxes: Tuple[QComboBox, QComboBox]
    spansComboBoxes: Tuple[QComboBox, QComboBox]
    startButton: QWidget

    def __init__(
        self,
        nodesComboBoxes: Tuple[QComboBox, QComboBox],
        spansComboBoxes: Tuple[QComboBox, QComboBox],
        startButton: QWidget,
    ):
        self.nodesComboBoxes = nodesComboBoxes
        self.spansComboBoxes = spansComboBoxes
        self.startButton = startButton

    def _populateSelectionDropdowns(self, layers: List[QgsVectorLayer]):
        # Populate the drop-down boxes (aka ComboBox) with the layers loaded into the project
        for ncb in self.nodesComboBoxes:
            ncb.clear()
            for layer in layers:
                ncb.addItem(layer.name(), layer)

        for scb in self.spansComboBoxes:
            scb.clear()
            for layer in layers:
                scb.addItem(layer.name(), layer)

    def update(self, state: ToolState):
        """
        Enable/Disable all the layer selection drop-down boxes and start button.
        We don't want the user to change layers in the middle of the process!
        """
        if isinstance(state, ToolLayerSelectState):
            self._populateSelectionDropdowns(state.selectableLayers)
            enable_layer_select = True
        else:
            enable_layer_select = False

        # Set the Enabled/Disabled state for our widgets
        for widget in self.nodesComboBoxes:
            widget.setEnabled(enable_layer_select)

        for widget in self.spansComboBoxes:
            widget.setEnabled(enable_layer_select)

        self.startButton.setEnabled(enable_layer_select)


class ComparisonView:
    """
    The view which renders the comparison part of the UI.
    """

    mapViews: Tuple[MiniMapView, MiniMapView]
    infoPanelViews: Tuple[InfoPanelView, InfoPanelView]

    sameButton: QPushButton
    notSameButton: QPushButton

    nextButton: QPushButton
    prevButton: QPushButton

    def __init__(
        self,
        project: QgsProject,
        canvases: Tuple[QgsMapCanvas, QgsMapCanvas],
        infoPanels: Tuple[QPlainTextEdit, QPlainTextEdit],
        sameButton: QPushButton,
        notSameButton: QPushButton,
        nextButton: QPushButton,
        prevButton: QPushButton,
    ):
        osmLayer = getOpenStreetMapLayer(project)
        self.mapViews = (
            MiniMapView(canvases[0], osmLayer),
            MiniMapView(canvases[1], osmLayer),
        )
        self.infoPanelViews = (
            InfoPanelView(infoPanels[0]),
            InfoPanelView(infoPanels[1]),
        )
        self.sameButton = sameButton
        self.notSameButton = notSameButton
        self.nextButton = nextButton
        self.prevButton = prevButton

    def _updateComparing(
        self, state: Union[ToolNodeComparisonState, ToolSpanComparisonState]
    ):
        """
        Update UI when we are currently comparing a pair of features.
        """
        for i in [0, 1]:
            self.mapViews[i].update(
                MiniMapView.State(
                    nodesLayer=state.networks[i].nodesLayer,
                    spansLayer=state.networks[i].spansLayer,
                    featureId=state.currentComparison.features[i].featureId,
                    featureType=state.currentComparison.features[i].featureType,
                )
            )

            self.infoPanelViews[i].update(state.currentComparison.features[i])

        outcome: Optional[FeatureComparisonOutcome] = state.currentOutcome
        if outcome is None:
            self.sameButton.setEnabled(True)
            self.notSameButton.setEnabled(True)

        else:
            self.sameButton.setEnabled(not outcome.areDuplicate)
            self.notSameButton.setEnabled(outcome.areDuplicate)

        self.nextButton.setEnabled(True)
        self.prevButton.setEnabled(True)

    def _updateNotComparing(self):
        """
        Disable comparison UI when comparison is not enabled e.g. we're still selecting
        layers, or comparison is already complete.
        """
        for mv in self.mapViews:
            mv.update(None)

        for ipv in self.infoPanelViews:
            ipv.update(None)

        self.sameButton.setEnabled(False)
        self.notSameButton.setEnabled(False)

        self.nextButton.setEnabled(False)
        self.prevButton.setEnabled(False)

    def update(self, state: ToolState):
        if isinstance(state, ToolNodeComparisonState) or isinstance(
            state, ToolSpanComparisonState
        ):
            self._updateComparing(state)
        else:
            self._updateNotComparing()


#
# Top-level view
#


class ToolView:
    """
    Top-level view which contains all other views.
    """

    layerSelectView: LayerSelectView
    comparisonView: ComparisonView

    def __init__(self, project: QgsProject, ui: Ui_OFDSDedupToolDialog):
        self.layerSelectView = LayerSelectView(
            nodesComboBoxes=(ui.nodesComboBoxA, ui.nodesComboBoxB),
            spansComboBoxes=(ui.spansComboBoxA, ui.spansComboBoxB),
            startButton=ui.startButton,
        )

        self.comparisonView = ComparisonView(
            project=project,
            canvases=(ui.mapA, ui.mapB),
            infoPanels=(ui.infoPanelA, ui.infoPanelB),
            sameButton=ui.sameButton,
            notSameButton=ui.notSameButton,
            nextButton=ui.nextButton,
            prevButton=ui.prevButton,
        )

    def update(self, state: ToolState):
        self.layerSelectView.update(state)
        self.comparisonView.update(state)
