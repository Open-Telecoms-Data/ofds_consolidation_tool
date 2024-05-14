import logging
from typing import List, Optional, Tuple, Union
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
from qgis.core import (
    QgsMapLayer,
    QgsVectorLayer,
    QgsProject,
    QgsCoordinateTransform,
    QgsWkbTypes,
)
from qgis.gui import QgsMapCanvas

from .model.comparison import (
    ConsolidationReason,
    NodeComparison,
    SpanComparison,
)
from ..gui import Ui_OFDSDedupToolDialog

from ..helpers import EPSG3857, getOpenStreetMapLayer
from .model.network import FeatureType
from .viewmodel.state import (
    ToolLayerSelectState,
    ToolNodeComparisonState,
    ToolOutputState,
    ToolSpanComparisonState,
    ToolState,
    ToolStateEnum,
)

logger = logging.getLogger(__name__)

# Scale ratio of the displayed minimaps when showing Nodes
# e.g. 1:25,000 would be 25000
MINIMAP_SCALE_RATIO = 100000  # 1:100,000


DISPLAY_NODE_PROPERTIES = [
    "id",
    "name",
    "phase/name",
    "physicalInfrastructureProvider/name",
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


DISPLAY_SPAN_PROPERTIES = [
    "id",
    "name",
    "phase/name",
    "readyForServiceDate",
    "start/name",
    "end/name",
    "physicalInfrastructureProvider/name",
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
        featureId: Optional[int]
        featureType: Optional[FeatureType]

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
            raise InvalidViewState("Can't display map without layers set")

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
            raise InvalidViewState("Unexpected Layer change")

        # Zoom the map to and hilight the relevent feature
        if state.featureType is not None and state.featureId is not None:
            if state.featureType == FeatureType.NODE:
                self.mapCanvas.zoomToFeatureIds(
                    self.layers.nodesLayer, [state.featureId]
                )
                self.layers.nodesLayer.selectByIds([state.featureId])
                self.mapCanvas.zoomScale(MINIMAP_SCALE_RATIO)

            elif state.featureType == FeatureType.SPAN:
                self.mapCanvas.zoomToFeatureIds(
                    self.layers.spansLayer, [state.featureId]
                )
                self.layers.spansLayer.selectByIds([state.featureId])

            else:
                raise InvalidViewState
        else:
            self.zoomToEverything()

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
        all_props = DISPLAY_NODE_PROPERTIES

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

    def render_span_comparison_info(self, comparison: SpanComparison) -> str:
        span_a = comparison.features[0]
        span_b = comparison.features[1]

        hi_score_props = set(comparison.get_high_scoring_properties())
        all_props = DISPLAY_SPAN_PROPERTIES

        hi_score_rows = [
            (prop, span_a.get(prop), span_b.get(prop), comparison.scores.get(prop, 0))
            for prop in hi_score_props
        ]

        all_score_rows = [
            (prop, span_a.get(prop), span_b.get(prop), comparison.scores.get(prop, 0))
            for prop in all_props
        ]

        info_html = f"""
        <h2>Overall Confidence: {int(comparison.confidence)}%</h2>

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

        elif isinstance(comparison, SpanComparison):
            self.infoPanel.setHtml(self.render_span_comparison_info(comparison))

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
                if layer.geometryType() == QgsWkbTypes.GeometryType.PointGeometry:
                    ncb.addItem(layer.name(), layer)

        for scb in self.spansComboBoxes:
            scb.clear()
            for layer in layers:
                if layer.geometryType() == QgsWkbTypes.GeometryType.LineGeometry:
                    scb.addItem(layer.name(), layer)

    def update(self, state: Optional[ToolState]):
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

    def _updateComparing(
        self, state: Union[ToolNodeComparisonState, ToolSpanComparisonState]
    ):
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

        outcome = state.currentOutcome
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
            else f"Span Comparison {state.current+1} of {state.nTotal}"
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

    def update(self, state: Optional[ToolState]):
        if isinstance(state, ToolNodeComparisonState):
            self._updateComparing(state)
        elif isinstance(state, ToolSpanComparisonState):
            self._updateComparing(state)
        else:
            self._updateNotComparing()


class OutputView:
    minimapview: MiniMapView

    # TODO: Add style!
    def __init__(self, project: QgsProject, mapCanvas: QgsMapCanvas):
        osmLayer = getOpenStreetMapLayer(project)
        self.minimapview = MiniMapView(mapCanvas=mapCanvas, backgroundLayer=osmLayer)

    def update(self, state: Optional[ToolState]):
        if isinstance(state, ToolOutputState):
            self.minimapview.update(
                MiniMapView.State(
                    nodesLayer=state.output_network.nodesLayer,
                    spansLayer=state.output_network.spansLayer,
                    featureId=None,
                    featureType=None,
                )
            )
        else:
            self.minimapview.update(None)


#
# Top-level view
#


class ToolView:
    """
    Top-level view which contains all other views.
    """

    layerSelectView: LayerSelectView
    nodeComparisonView: ComparisonView
    outputView: OutputView
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

        self.outputView = OutputView(project=project, mapCanvas=ui.outputMapCanvas)

        self.tabWidget = ui.tabWidget

    def update(self, state: Optional[ToolState]):
        if isinstance(state, ToolLayerSelectState):
            self.tabWidget.setCurrentIndex(0)
            self.layerSelectView.update(state)
        else:
            self.layerSelectView.update(None)

        if isinstance(state, ToolNodeComparisonState):
            self.tabWidget.setCurrentIndex(1)
            self.nodeComparisonView.update(state)
        else:
            self.nodeComparisonView.update(None)

        if isinstance(state, ToolSpanComparisonState):
            self.tabWidget.setCurrentIndex(2)
            self.spanComparisonView.update(state)
        else:
            self.spanComparisonView.update(None)

        if isinstance(state, ToolOutputState):
            self.tabWidget.setCurrentIndex(3)
            self.outputView.update(state)
        else:
            self.outputView.update(None)
