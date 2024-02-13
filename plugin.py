import logging
import sys

from PyQt5.QtCore import PYQT_VERSION_STR, QT_VERSION_STR
from PyQt5.QtWidgets import QAction
from qgis.core import QgsMapLayer, QgsProject

from .tool import OFDSDedupToolDialog

logger = logging.getLogger(__name__)


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
        logger.debug("Running OFDS Consolidation plugin")
        logger.debug(
            f"Qt: v{QT_VERSION_STR} PyQt: v{PYQT_VERSION_STR} Python: {sys.version}"
        )

        project = QgsProject.instance()
        if not project:
            raise Exception

        self.tool_dialog.reset(project=project)
        self.tool_dialog.show()
