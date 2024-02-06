import os
from pathlib import Path

from PyQt5.QtWidgets import QAction, QMessageBox, QWidget, QDialog
from PyQt5.QtCore import QRect
from qgis.core import QgsVectorLayer, QgsRasterLayer
from qgis.gui import (
    QgsMapCanvas,
    QgsVertexMarker,
    QgsMapCanvasItem,
    QgsMapMouseEvent,
    QgsRubberBand,
)
from .gui import Ui_OFDSDedupToolDialog

DATA_PATH = Path(os.environ.get("OFDS_DATA_PATH")) / "brazil_network_spans.geojson"

class OFDSDedupToolDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.ui = Ui_OFDSDedupToolDialog()
        self.ui.setupUi(self)

class OFDSDedupPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.tool_dialog = OFDSDedupToolDialog()

    def initGui(self):
        self.action = QAction("Consolidate OFDS", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        self.iface.removeToolBarIcon(self.action)
        del self.action

    def run(self):
        logger.info("Running OFDS Consolidation plugin")

        print("Running OFDS Consolidation plugin")
        self.tool_dialog.show()

        osm_tms = "type=xyz&url=https://tile.openstreetmap.org/{z}/{x}/{y}.png&zmax=19&zmin=0&http-header:referer="
        osm_layer = QgsRasterLayer(osm_tms, "OSM", "wms")

        vlayer = QgsVectorLayer(DATA_PATH.as_posix(), "Kenya Spans", "ogr")

        canvas_left = self.tool_dialog.ui.canvas_left

        canvas_left.setExtent(vlayer.extent())
        canvas_left.setLayers([vlayer, osm_layer])
