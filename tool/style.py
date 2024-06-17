import logging
from typing import List, cast

from PyQt5.QtWidgets import QDialog
from qgis.core import (
    QgsProject,
    QgsMapLayer,
    QgsWkbTypes,
    QgsVectorLayer,
    QgsMapLayerType,
)

from ..resources import STYLESHEET_NODES, STYLESHEET_SPANS
from ..gui_style import Ui_StyleOFDSDialog

logger = logging.getLogger(__name__)


class OFDSStyleToolDialog(QDialog):
    """
    The top-level GUI element, the Dialog box that holds all our other sub-elements.

    Note that there is a singleton instance of this class, it isn't created/destroyed
    each time we open the tool, but it remains constantly "open" in the backgroud even
    when closed or hidden, and all state is still the same next time the tool is opened
    from the toolbar. This means it's important to properly tidy up the GUI and any
    created/opened resources when we're done.
    """

    ui: Ui_StyleOFDSDialog

    def __init__(self):
        super().__init__()

        self.ui = Ui_StyleOFDSDialog()
        self.ui.setupUi(self)

        # Connect UI signals to slots on this class
        self.ui.nodesApplyButton.pressed.connect(self.apply_nodes_style)
        self.ui.spansApplyButton.pressed.connect(self.apply_spans_style)
        self.ui.refreshButton.pressed.connect(self.refresh_layers)

    def refresh_layers(self):
        """Refresh and populate the lists of layers from the current Project"""

        project = QgsProject.instance()

        # Find all the layers the user has loaded
        all_layers: List[QgsMapLayer] = project.mapLayers(validOnly=True).values()

        # Filter the layers that the tool can accept
        selectable_layers: List[QgsVectorLayer] = list()

        for layer in all_layers:
            # only vector layers can be valid OFDS layers
            if layer.type() == QgsMapLayerType.VectorLayer:
                selectable_layers.append(cast(QgsVectorLayer, layer))

        ncb = self.ui.nodesComboBox
        scb = self.ui.spansComboBox

        ncb.clear()
        for layer in selectable_layers:
            if layer.geometryType() == QgsWkbTypes.GeometryType.PointGeometry:
                ncb.addItem(layer.name(), layer)

        scb.clear()
        for layer in selectable_layers:
            if layer.geometryType() == QgsWkbTypes.GeometryType.LineGeometry:
                scb.addItem(layer.name(), layer)

    def apply_nodes_style(self):
        """Apply the Nodes style to the currently selected Nodes layer"""
        nodes_layer = self.ui.nodesComboBox.currentData()
        if isinstance(nodes_layer, QgsVectorLayer):
            if nodes_layer.geometryType() == QgsWkbTypes.GeometryType.PointGeometry:
                nodes_layer.loadNamedStyle(STYLESHEET_NODES.as_posix(), False)
                nodes_layer.triggerRepaint()

    def apply_spans_style(self):
        """Apply the Spans style to the currently selected Spans layer"""
        spans_layer = self.ui.spansComboBox.currentData()
        if isinstance(spans_layer, QgsVectorLayer):
            if spans_layer.geometryType() == QgsWkbTypes.GeometryType.LineGeometry:
                spans_layer.loadNamedStyle(STYLESHEET_SPANS.as_posix(), False)
                spans_layer.triggerRepaint()
