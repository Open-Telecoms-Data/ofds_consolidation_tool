import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple, Union, Set

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

from .helpers import EPSG3857, getOpenStreetMapLayer
from .model.comparison import (
    ConsolidationReason,
    NodeComparison,
    SpanComparison,
)
from .model.network import FeatureType
from .viewmodel.state import (
    ToolLayerSelectState,
    ToolNodeComparisonState,
    ToolOutputState,
    ToolSpanComparisonState,
    ToolState,
    ToolStateEnum,
)
from ..gui import Ui_OFDSDedupToolDialog
from .helpers import EPSG3857, getOpenStreetMapLayer
from ..resources import STYLESHEET_NODES, STYLESHEET_SPANS

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
            logger.debug("RESET MAP")
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

        exact_match_rows = [row for row in hi_score_rows if row[3] == 1]
        strong_match_rows = [row for row in hi_score_rows if row not in exact_match_rows]
        zero_score_rows = [row for row in all_score_rows if row[3] == 0]
        missing_data_rows = [row for row in zero_score_rows if
                             row[1] is None or row[1] is [] or row[2] is None or row[2] is []]
        low_score_rows = [row for row in all_score_rows if
                          row[0] not in hi_score_props and row[3] > 0 and row not in missing_data_rows]

        # Display Node info
        info_html = f"""
        <h2>Overall Confidence: {int(comparison.confidence)}%</h2>

        <p>Distance between nodes (km): {comparison.distance_km:.2f}</p>

        <h2>Confidence score details</h2>
        """

        if len(exact_match_rows) > 0:
            info_html = info_html + f"""
        <h3>Exact matches</h3>
        <p>These properties are exactly the same on both nodes:</p>
        <table>
          <tr>
            <th align="left">Property</th>
            <th align="left">Value</th>
          </tr>
          {
            "".join(f"<tr><td>{k}</td><td>{va}</td></tr>" for k, va, _, _ in exact_match_rows)
            }
        </table>
            """

        if len(strong_match_rows) > 0:
            info_html = info_html + f"""
        <h3>Strong matches</h3>
        <p>These properties are very similar in both networks for this node:</p>
        <table>
          <tr>
            <th align="left">Property</th>
            <th align="left">Primary</th>
            <th align="left">Secondary</th>
            <th align="left">Confidence</th>
          </tr>
          {
            "".join(f"<tr><td>{k}</td><td>{va}</td><td>{vb}</td><td>{int(sc * 100)}%</td></tr>"
                    for k, va, vb, sc in strong_match_rows)
            }
        </table>
            """

        if len(low_score_rows) > 0:
            info_html = info_html + f"""

        <h3>Unlikely matches</h3>
        <p>These properties are not similar in both networks for this node:</p>
        <table>
          <tr>
            <th align="left">Property</th>
            <th align="left">Primary</th>
            <th align="left">Secondary</th>
            <th align="left">Confidence</th>
          </tr>
          {
            "".join(f"<tr><td>{k}</td><td>{va}</td><td>{vb}</td><td>{int(sc * 100)}%</td></tr>"
                    for k, va, vb, sc in low_score_rows)
            }
        </table>
        """

        if len(missing_data_rows) > 0:
            info_html = info_html + f"""
        <h3>Missing data</h3>
        <p>These properties are missing from one or both of the networks for this node:</p>
        <ul>
        {
            "".join(f"<li>{k}</li>" for k, _, _, _ in missing_data_rows)
            }
        </ul>
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

        exact_match_rows = [row for row in hi_score_rows if row[3] == 1]
        strong_match_rows = [row for row in hi_score_rows if row not in exact_match_rows]
        zero_score_rows = [row for row in all_score_rows if row[3] == 0]
        missing_data_rows = [row for row in zero_score_rows if
                             row[1] is None or row[1] is [] or row[2] is None or row[2] is []]
        low_score_rows = [row for row in all_score_rows if
                          row[0] not in hi_score_props and row[3] > 0 and row not in missing_data_rows]

        info_html = f"""
        <h2>Overall Confidence: {int(comparison.confidence)}%</h2>

        <p>These spans start and end at the same nodes.</p>

        <h2>Confidence score details</h2>
        """

        if len(exact_match_rows) > 0:
            info_html = info_html + f"""
        <h3>Exact matches</h3>

        <p>These properties are exactly the same on both spans:</p>
        <table>
          <tr>
            <th align="left">Property</th>
            <th align="left">Value</th>
          </tr>
          {
            "".join(f"<tr><td>{k}</td><td>{va}</td></tr>" for k, va, _, _ in exact_match_rows)
            }
        </table>
            """

        if len(strong_match_rows) > 0:
            info_html = info_html + f"""
        <h3>Strong matches</h3>
        <p>These properties are very similar in both networks for this span:</p>
        <table>
          <tr>
            <th align="left">Property</th>
            <th align="left">Primary</th>
            <th align="left">Secondary</th>
            <th align="left">Confidence</th>
          </tr>
          {
            "".join(f"<tr><td>{k}</td><td>{va}</td><td>{vb}</td><td>{int(sc * 100)}%</td></tr>"
                    for k, va, vb, sc in strong_match_rows)
            }
        </table>
            """

        if len(low_score_rows) > 0:
            info_html = info_html + f"""

        <h3>Unlikely matches</h3>
        <p>These properties are not similar in both networks for this span:</p>
        <table>
          <tr>
            <th align="left">Property</th>
            <th align="left">Primary</th>
            <th align="left">Secondary</th>
            <th align="left">Confidence</th>
          </tr>
          {
            "".join(f"<tr><td>{k}</td><td>{va}</td><td>{vb}</td><td>{int(sc * 100)}%</td></tr>"
                    for k, va, vb, sc in low_score_rows)
            }
        </table>
        """

        if len(missing_data_rows) > 0:
            info_html = info_html + f"""
        <h3>Missing data</h3>
        <p>These properties are missing from one or both of the networks for this span:</p>
        <ul>
        {
            "".join(f"<li>{k}</li>" for k, _, _, _ in missing_data_rows)
            }
        </ul>
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
    networksComboBoxes: Tuple[QComboBox, QComboBox]
    startButton: QWidget

    _previous_networks: Tuple[List[Tuple[str, str]], List[Tuple[str, str]]]
    _previous_layers_ids: Set[str]

    def __init__(
            self,
            nodesComboBoxes: Tuple[QComboBox, QComboBox],
            spansComboBoxes: Tuple[QComboBox, QComboBox],
            networksComboBoxes: Tuple[QComboBox, QComboBox],
            startButton: QWidget,
    ):
        self.nodesComboBoxes = nodesComboBoxes
        self.spansComboBoxes = spansComboBoxes
        self.networksComboBoxes = networksComboBoxes
        self.startButton = startButton
        self._previous_networks = ([], [])
        self._previous_layers_ids = set()

    def _populateSelectionDropdowns(self, state: ToolLayerSelectState, layers: List[QgsVectorLayer]):
        # Populate the drop-down boxes (aka ComboBox)
        # with the layers loaded into the project
        #
        # WARNING: Only update ComboBoxes if the list of layers hasn't changed, or else infinite loop ensues.
        layers_ids: Set[str] = set(l.id() for l in layers)
        if layers_ids == self._previous_layers_ids:
            return

        # Important flag to not accidentally cause recursive updates
        # BEGIN
        state._is_populating_layers = True

        nodes_layers = [ layer for layer in layers if layer.geometryType() == QgsWkbTypes.GeometryType.PointGeometry]
        spans_layers = [ layer for layer in layers if layer.geometryType() == QgsWkbTypes.GeometryType.LineGeometry]

        for ncb in self.nodesComboBoxes:
            ncb.clear()
            for layer in nodes_layers:
                ncb.addItem(layer.name(), layer)

        for scb in self.spansComboBoxes:
            scb.clear()
            for layer in spans_layers:
                scb.addItem(layer.name(), layer)

        self._previous_layers_ids = layers_ids

        # END
        state._is_populating_layers = False

        # Find Network IDs for the selected layers and update the Network selection list
        nodes_layer_a: Optional[QgsVectorLayer] = self.nodesComboBoxes[0].currentData()
        spans_layer_a: Optional[QgsVectorLayer] = self.spansComboBoxes[0].currentData()

        nodes_layer_b: Optional[QgsVectorLayer] = self.nodesComboBoxes[1].currentData()
        spans_layer_b: Optional[QgsVectorLayer] = self.spansComboBoxes[1].currentData()

        return state.update_networks_list((nodes_layer_a, nodes_layer_b), (spans_layer_a, spans_layer_b))

    def update(self, state: Optional[ToolState]):
        """
        Enable/Disable all the layer selection drop-down boxes and start button.
        We don't want the user to change layers in the middle of the process!
        """
        if isinstance(state, ToolLayerSelectState):
            if state._is_populating_layers is True:
                return  # Prevent recursive updates

            self._populateSelectionDropdowns(state, state.selectableLayers)

            enable_layer_select = True

            # Enable & populate the Network Selection dropdowns if they've already selected layers
            if enable_layer_select and len(state.selectableNetworksA) > 0:
                self.networksComboBoxes[0].setEnabled(True)
                if set(self._previous_networks[0]) != set(state.selectableNetworksA):
                    self.networksComboBoxes[0].clear()
                    for (net_id, net_name) in state.selectableNetworksA:
                        self.networksComboBoxes[0].addItem(f"{net_name} ({net_id})", net_id)
            else:
                self.networksComboBoxes[0].setEnabled(False)
                self.networksComboBoxes[0].clear()

            if enable_layer_select and len(state.selectableNetworksB) > 0:
                self.networksComboBoxes[1].setEnabled(True)
                if set(self._previous_networks[1]) != set(state.selectableNetworksB):
                    self.networksComboBoxes[1].clear()
                    for (net_id, net_name) in state.selectableNetworksB:
                        self.networksComboBoxes[1].addItem(f"{net_name} ({net_id})", net_id)
            else:
                self.networksComboBoxes[1].setEnabled(False)
                self.networksComboBoxes[1].clear()

            self._previous_networks = (state.selectableNetworksA.copy(), state.selectableNetworksB.copy())

        else:
            enable_layer_select = False
            self.networksComboBoxes[0].setEnabled(False)
            self.networksComboBoxes[0].clear()
            self.networksComboBoxes[1].setEnabled(False)
            self.networksComboBoxes[1].clear()

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
            self.sameButton.setStyleSheet("background-color: white;")
            self.notSameButton.setEnabled(True)
            self.notSameButton.setStyleSheet("background-color: white;")

        elif isinstance(outcome.consolidate, ConsolidationReason):
            self.sameButton.setEnabled(False)
            self.sameButton.setStyleSheet("background-color: yellow;")
            self.notSameButton.setEnabled(True)
            self.notSameButton.setStyleSheet("background-color: white;")

        elif outcome.consolidate is False:
            self.sameButton.setEnabled(True)
            self.sameButton.setStyleSheet("background-color: white;")
            self.notSameButton.setEnabled(False)
            self.notSameButton.setStyleSheet("background-color: yellow;")

        self.nextButton.setEnabled(True)
        self.prevButton.setEnabled(True)

        self.progressLabel.setText(
            f"Node Comparison {state.current + 1} of {state.nTotal}"
            if state.state == ToolStateEnum.COMPARING_NODES
            else f"Span Comparison {state.current + 1} of {state.nTotal}"
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
            state.output_network.nodesLayer.loadNamedStyle(STYLESHEET_NODES.as_posix())
            state.output_network.spansLayer.loadNamedStyle(STYLESHEET_SPANS.as_posix())

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
            networksComboBoxes=(ui.networkComboBoxA, ui.networkComboBoxB),
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
