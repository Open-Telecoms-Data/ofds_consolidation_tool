import logging
import sys

from PyQt5.QtCore import PYQT_VERSION_STR, QT_VERSION_STR
from PyQt5.QtWidgets import QAction
from qgis.core import QgsProject
from qgis.utils import iface  # type: ignore

from .tool.tool import OFDSDedupToolDialog

logger = logging.getLogger(__name__)


class OFDSDedupPlugin:
    def __init__(self):
        self.tool_dialog = OFDSDedupToolDialog()

    def initGui(self):
        self.action = QAction("Consolidate OFDS", iface.mainWindow())
        self.action.setObjectName("consolidateOfdsAction")
        self.action.triggered.connect(self.run)
        iface.addToolBarIcon(self.action)
        iface.addPluginToMenu("&Consolidate OFDS", self.action)

    def unload(self):
        iface.removeToolBarIcon(self.action)
        iface.removePluginToMenu("&Consolidate OFDS", self.action)
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
