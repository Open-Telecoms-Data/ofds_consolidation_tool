import logging
from typing import List, Optional, Tuple, Union
import json
from dataclasses import dataclass
from PyQt5.QtWidgets import (
    QTextEdit,
    QPushButton,
    QWidget,
    QComboBox,
    QLabel,
    QProgressBar,
    QTabWidget,
)
from qgis.core import QgsMapLayer, QgsVectorLayer, QgsProject, QgsCoordinateTransform
from qgis.gui import QgsMapCanvas

from .model.comparison import (
    ALL_NODE_PROPERTIES,
    ConsolidationReason,
    NodeComparison,
    SpanComparison,
)
from ..gui import Ui_OFDSDedupToolDialog

from ..helpers import EPSG3857, getOpenStreetMapLayer
from .model.network import Span, FeatureType
from .model.comparison import ComparisonOutcome
from .viewmodel.state import (
    ToolLayerSelectState,
    ToolNodeComparisonState,
    ToolSpanComparisonState,
    ToolState,
    ToolStateEnum,
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

    def zoomToEverything(self):
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
            self.zoomToEverything()

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
            self.mapCanvas.zoomScale(25000.0)

        elif state.featureType == FeatureType.SPAN:
            self.mapCanvas.zoomToFeatureIds(self.layers.spansLayer, [state.featureId])
            self.layers.spansLayer.selectByIds([state.featureId])

        else:
            raise InvalidViewState

        # We need to "refresh" to rerender the map after changing it
        self.mapCanvas.refresh()


class InfoPanelView:
    infoPanel: QTextEdit

    def __init__(self, infoPanel: QTextEdit):
        self.infoPanel = infoPanel

    def render_node_comparison_info_html(self, comparison: NodeComparison) -> str:
        """
        Returns HTML to display in the info panel when comparing two nodes.
        """

        node_a = comparison.features[0]
        node_b = comparison.features[1]

        hi_score_props = set(comparison.get_high_scoring_properties())
        all_props = ALL_NODE_PROPERTIES

        hi_score_rows = [
            (prop, node_a.get(prop), node_b.get(prop), comparison.scores.get(prop, 0))
            for prop in hi_score_props
        ]

        all_score_rows = [
            (prop, node_a.get(prop), node_b.get(prop), comparison.scores.get(prop, 0))
            for prop in all_props
        ]

        # Display Node info
        info_html = f"""
        <h2>Overall Confidence: {int(comparison.confidence)}%</h2>

        <p>Distance (km): {comparison.distance_km:.2f}</p>

        <h2>Similar Properties</h2>


        <table>
          <tr>
            <th>Attribute</th>
            <th>Value A</th>
            <th>Value B</th>
            <th>Score</th>
          </tr>
          {
              "".join(f"<tr><td>{k}</td><td>{va}</td><td>{vb}</td><td>{int(sc*100)}%</td></tr>"
                      for k,va,vb,sc in hi_score_rows)
          }
        </table>

        <h2>All Properties</h2>

        <table>
          <tr>
            <th>Attribute</th>
            <th>Value A</th>
            <th>Value B</th>
            <th>Score</th>
          </tr>
          {
              "".join(f"<tr><td>{k}</td><td>{va}</td><td>{vb}</td><td>{int(sc*100)}%</td></tr>"
                      for k,va,vb,sc in all_score_rows)
          }
        </table>
        """

        return info_html

    def update(self, comparison: Union[NodeComparison, SpanComparison, None]):
        """
        Display the given Comparison, or nothing.
        """
        if comparison is None:
            # No feature to display, e.g. still selecting layers
            self.infoPanel.setHtml("")
            self.infoPanel.setEnabled(False)
            return

        # Display feature info

        self.infoPanel.setEnabled(True)
        if isinstance(comparison, NodeComparison):

            self.infoPanel.setHtml(self.render_node_comparison_info_html(comparison))

        elif isinstance(comparison, Span):
            # Display Span info
            # TODO: make prettier. Maybe use non-plaintext
            self.infoPanel.setHtml(json.dumps(comparison.properties, indent=2))

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
        # Populate the drop-down boxes (aka ComboBox)
        # with the layers loaded into the project
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
    infoPanelView: InfoPanelView

    sameButton: QPushButton
    notSameButton: QPushButton

    nextButton: QPushButton
    prevButton: QPushButton

    progressLabel: QLabel
    progressBar: QProgressBar

    finishButton: QPushButton

    def __init__(
        self,
        project: QgsProject,
        canvases: Tuple[QgsMapCanvas, QgsMapCanvas],
        infoPanel: QTextEdit,
        sameButton: QPushButton,
        notSameButton: QPushButton,
        nextButton: QPushButton,
        prevButton: QPushButton,
        progressLabel: QLabel,
        progressBar: QProgressBar,
        finishButton: QPushButton,
    ):
        osmLayer = getOpenStreetMapLayer(project)
        self.mapViews = (
            MiniMapView(canvases[0], osmLayer),
            MiniMapView(canvases[1], osmLayer),
        )
        self.infoPanelView = InfoPanelView(infoPanel)
        self.sameButton = sameButton
        self.notSameButton = notSameButton
        self.nextButton = nextButton
        self.prevButton = prevButton
        self.progressLabel = progressLabel
        self.progressBar = progressBar
        self.finishButton = finishButton

    def _updateComparing(self, state: ToolNodeComparisonState):
        """
        Update UI when we are currently comparing a pair of features.
        """
        if state.currentComparison is None:
            for i in [0, 1]:
                self.mapViews[i].zoomToEverything()
        else:
            for i in [0, 1]:
                self.mapViews[i].update(
                    MiniMapView.State(
                        nodesLayer=state.networks[i].nodesLayer,
                        spansLayer=state.networks[i].spansLayer,
                        featureId=state.currentComparison.features[i].featureId,
                        featureType=state.currentComparison.features[i].featureType,
                    )
                )

        self.infoPanelView.update(state.currentComparison)

        outcome: Optional[ComparisonOutcome] = state.currentOutcome
        if outcome is None:
            self.sameButton.setEnabled(True)
            self.notSameButton.setEnabled(True)

        else:
            self.sameButton.setEnabled(
                not isinstance(outcome.consolidate, ConsolidationReason)
            )
            self.notSameButton.setEnabled(not (outcome.consolidate is False))

        self.nextButton.setEnabled(True)
        self.prevButton.setEnabled(True)

        self.progressLabel.setText(
            f"Node Comparison {state.current+1} of {state.nTotal}"
            if state.state == ToolStateEnum.COMPARING_NODES
            else "Span"
        )
        self.progressBar.setEnabled(True)
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(state.nTotal)
        self.progressBar.setValue(state.nCompared)
        self.progressBar.setFormat("%v of %m compared")

        self.finishButton.setEnabled(True)

    def _updateNotComparing(self):
        """
        Disable comparison UI when comparison is not enabled e.g. we're still selecting
        layers, or comparison is already complete.
        """
        for mv in self.mapViews:
            mv.update(None)

        self.infoPanelView.update(None)

        self.sameButton.setEnabled(False)
        self.notSameButton.setEnabled(False)

        self.nextButton.setEnabled(False)
        self.prevButton.setEnabled(False)

        self.progressLabel.setText("")
        self.progressBar.setEnabled(False)
        self.progressBar.setFormat("")

        self.finishButton.setEnabled(False)

    def update(self, state: ToolState):
        if isinstance(state, ToolNodeComparisonState):
            self._updateComparing(state)
        elif isinstance(state, ToolSpanComparisonState):
            raise NotImplementedError
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
    nodeComparisonView: ComparisonView
    tabWidget: QTabWidget

    def __init__(self, project: QgsProject, ui: Ui_OFDSDedupToolDialog):
        self.layerSelectView = LayerSelectView(
            nodesComboBoxes=(ui.nodesComboBoxA, ui.nodesComboBoxB),
            spansComboBoxes=(ui.spansComboBoxA, ui.spansComboBoxB),
            startButton=ui.startButton,
        )

        self.nodeComparisonView = ComparisonView(
            project=project,
            canvases=(ui.mapA, ui.mapB),
            infoPanel=ui.infoPanel,
            sameButton=ui.sameNodesButton,
            notSameButton=ui.notSameNodesButton,
            nextButton=ui.nextNodesButton,
            prevButton=ui.prevNodesButton,
            progressLabel=ui.comparisonLabel,
            progressBar=ui.comparisonProgressBar,
            finishButton=ui.finishedNodesButton,
        )

        self.spanComparisonView = ComparisonView(
            project=project,
            canvases=(ui.spansMapA, ui.spansMapB),
            infoPanel=ui.spansInfoPanel,
            sameButton=ui.spansSameButton,
            notSameButton=ui.spansNotSameButton,
            nextButton=ui.spansNextButton,
            prevButton=ui.spansPrevButton,
            progressLabel=ui.spansComparisonLabel,
            progressBar=ui.spansComparisonProgressBar,
            finishButton=ui.spansFinishedButton,
        )

        self.tabWidget = ui.tabWidget

    def update(self, state: ToolState):
        if isinstance(state, ToolLayerSelectState):
            self.tabWidget.setCurrentIndex(0)

        elif isinstance(state, ToolNodeComparisonState):
            self.tabWidget.setCurrentIndex(1)

        elif isinstance(state, ToolSpanComparisonState):
            self.tabWidget.setCurrentIndex(2)

        else:
            raise NotImplementedError

        self.layerSelectView.update(state)
        self.nodeComparisonView.update(state)
