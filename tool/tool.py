import logging

from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QDialog
from qgis.core import (
    QgsProject,
)

from ..gui import Ui_OFDSDedupToolDialog

from .control import ToolController
from .viewmodel.state import ToolState
from .view import ToolView


logger = logging.getLogger(__name__)


class OFDSDedupToolDialog(QDialog):
    """
    The top-level GUI element, the Dialog box that holds all our other sub-elements.

    Note that there is a singleton instance of this class, it isn't created/destroyed
    each time we open the tool, but it remains constantly "open" in the backgroud even
    when closed or hidden, and all state is still the same next time the tool is opened
    from the toolbar. This means it's important to properly tidy up the GUI and any
    created/opened resources when we're done.
    """

    ui: Ui_OFDSDedupToolDialog
    project: QgsProject

    state: ToolState
    controller: ToolController
    view: ToolView

    def __init__(self):
        super().__init__()

        self.ui = Ui_OFDSDedupToolDialog()
        self.ui.setupUi(self)

        # Don't allow the user to switch tabs
        self.ui.tabWidget.tabBar().setEnabled(False)

        # Connect UI signals to slots on this class
        self.ui.startButton.clicked.connect(self.onStartButtonClicked)

        self.ui.sameNodesButton.clicked.connect(self.onSameNodeButtonClicked)
        self.ui.notSameNodesButton.clicked.connect(self.onNotSameNodeButtonClicked)
        self.ui.nextNodesButton.clicked.connect(self.onNextNodesButtonClicked)
        self.ui.prevNodesButton.clicked.connect(self.onPrevNodesButtonClicked)
        self.ui.finishedNodesButton.clicked.connect(self.onFinishedNodesButtonClicked)

        self.ui.spansSameButton.clicked.connect(self.onSameSpanButtonClicked)
        self.ui.spansNotSameButton.clicked.connect(self.onNotSameSpanButtonClicked)
        self.ui.spansNextButton.clicked.connect(self.onNextSpansButtonClicked)
        self.ui.spansPrevButton.clicked.connect(self.onPrevSpansButtonClicked)
        self.ui.spansFinishedButton.clicked.connect(self.onFinishedSpansButtonClicked)

        self.ui.outputSaveNodes.clicked.connect(self.onSaveNodesButtonClicked)
        self.ui.outputSaveSpans.clicked.connect(self.onSaveSpansButtonClicked)

    def reset(self, project: QgsProject):
        """
        Resets the tool to be ready to consolidate a new pair of networks.
        """
        self.project = project

        # Setup View/Controller
        self.controller = ToolController(self.project, self.ui)
        self.view = ToolView(self.project, self.ui)

        # Set initial state
        self.set_state(self.controller.onInit())

    def set_state(self, state: ToolState):
        self.state = state
        logger.debug(f"STATE = {self.state}")
        self.view.update(self.state)

    def onStartButtonClicked(self):
        logger.debug("Start button clicked")
        self.set_state(self.controller.onStartButton(self.state))

    # Nodes Comparison
    def onSameNodeButtonClicked(self):
        logger.debug("Same node button clicked")
        self.set_state(self.controller.onSameButton(self.state))

    def onNotSameNodeButtonClicked(self):
        logger.debug("Not Same node button clicked")
        self.set_state(self.controller.onNotSameButton(self.state))

    def onNextNodesButtonClicked(self):
        self.set_state(self.controller.onNextButton(self.state))

    def onPrevNodesButtonClicked(self):
        self.set_state(self.controller.onPrevButton(self.state))

    def onFinishedNodesButtonClicked(self):
        self.set_state(self.controller.onFinishedButton(self.state))

    # Spans Comparison
    def onSameSpanButtonClicked(self):
        self.set_state(self.controller.onSameButton(self.state))

    def onNotSameSpanButtonClicked(self):
        self.set_state(self.controller.onNotSameButton(self.state))

    def onNextSpansButtonClicked(self):
        self.set_state(self.controller.onNextButton(self.state))

    def onPrevSpansButtonClicked(self):
        self.set_state(self.controller.onPrevButton(self.state))

    def onFinishedSpansButtonClicked(self):
        self.set_state(self.controller.onFinishedButton(self.state))

    def onSaveNodesButtonClicked(self):
        self.set_state(self.controller.onSaveNodesButton(self.state))

    def onSaveSpansButtonClicked(self):
        self.set_state(self.controller.onSaveSpansButton(self.state))


class Worker(QThread):
    """Background thread for processing data without freezing the UI."""

    # TODO: todo
    pass
