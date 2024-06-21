import logging
import sys

from PyQt5.QtCore import PYQT_VERSION_STR, QT_VERSION_STR
from PyQt5.QtWidgets import QAction
from qgis.core import QgsProject
from qgis.gui import QgisInterface
from qgis.utils import iface

iface: QgisInterface

from .tool.tool import OFDSDedupToolDialog
from .tool.style import OFDSStyleToolDialog
from . import __version__

logger = logging.getLogger(__name__)


class OFDSDedupPlugin:
    def __init__(self):
        self.consolidate_tool_dialog = OFDSDedupToolDialog()
        self.style_tool_dialog = OFDSStyleToolDialog()

    def initGui(self):
        self.action_consolidate = QAction("Consolidate OFDS", iface.mainWindow())
        self.action_consolidate.setObjectName("consolidateOfdsAction")
        self.action_consolidate.triggered.connect(self.run_consolidate)
        iface.addToolBarIcon(self.action_consolidate)
        iface.addPluginToMenu("&OFDS", self.action_consolidate)

        self.action_style = QAction("Style OFDS", iface.mainWindow())
        self.action_style.setObjectName("styleOfdsAction")
        self.action_style.triggered.connect(self.run_style)
        iface.addToolBarIcon(self.action_style)
        iface.addPluginToMenu("&OFDS", self.action_style)

    def unload(self):
        iface.removePluginMenu("&OFDS", self.action_consolidate)
        iface.removeToolBarIcon(self.action_consolidate)
        del self.action_consolidate

        iface.removePluginMenu("&OFDS", self.action_style)
        iface.removeToolBarIcon(self.action_style)
        del self.action_style

        self.consolidate_tool_dialog.close()
        del self.consolidate_tool_dialog

        self.style_tool_dialog.close()
        del self.style_tool_dialog

    def run_consolidate(self):
        logger.debug("Opening OFDS Consolidate Tool Dialog")
        logger.debug(f"OFDS Consolidation Tool Plugin v{__version__}")
        logger.debug(
            f"Qt: v{QT_VERSION_STR} PyQt: v{PYQT_VERSION_STR} Python: {sys.version}"
        )

        project = QgsProject.instance()
        if not project:
            raise Exception

        self.consolidate_tool_dialog.reset(project=project)
        self.consolidate_tool_dialog.show()

    def run_style(self):
        logger.debug("Opening OFDS Style Tool Dialog")
        logger.debug(f"OFDS Consolidation Tool Plugin v{__version__}")
        project = QgsProject.instance()
        if not project:
            raise Exception

        self.style_tool_dialog.refresh_layers()
        self.style_tool_dialog.show()
