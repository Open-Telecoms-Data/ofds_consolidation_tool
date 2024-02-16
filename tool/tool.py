import logging

from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QDialog
from qgis.core import (
    QgsProject,
)

from ..gui import Ui_OFDSDedupToolDialog

from .control import ToolController
from .state import ToolState
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

        # Connect UI signals to slots on this class
        self.ui.startButton.clicked.connect(self.onStartButtonClicked)
        self.ui.sameButton.clicked.connect(self.onSameButtonClicked)
        self.ui.notSameButton.clicked.connect(self.onNotSameButtonClicked)
        self.ui.nextButton.clicked.connect(self.onNextButtonClicked)
        self.ui.prevButton.clicked.connect(self.onPrevButtonClicked)
        self.ui.buttons.clicked.connect(self.onOkCancelButtonClicked)

    def reset(self, project: QgsProject):
        """
        Resets the tool to be ready to consolidate a new pair of networks.
        """
        self.project = project

        # Setup MVC
        self.controller = ToolController(self.project, self.ui)
        self.view = ToolView(self.project, self.ui)

        # Set initial state
        self.update(self.controller.onInit())

    def update(self, state: ToolState):
        self.state = state
        self.view.update(self.state)

    def onStartButtonClicked(self):
        logger.debug("Start button clicked")
        self.update(self.controller.onStartButton(self.state))

    def onSameButtonClicked(self):
        logger.debug("Same button clicked")
        self.update(self.controller.onSameButton(self.state))

    def onNotSameButtonClicked(self):
        logger.debug("Not Same button clicked")
        self.update(self.controller.onNotSameButton(self.state))

    def onNextButtonClicked(self):
        self.update(self.controller.onNextButton(self.state))

    def onPrevButtonClicked(self):
        self.update(self.controller.onPrevButton(self.state))

    def onOkCancelButtonClicked(self):
        logger.debug("OK or Cancel button clicked")
        self.reset(self.project)


class Worker(QThread):
    """Background thread for processing data without freezing the UI."""

    # TODO: todo
    pass
