from PyQt5.QtCore import QObject

from ..gui import Ui_OFDSDedupToolDialog
from .state import ToolState


class ControllerInvalidState(Exception):
    pass


class ToolController(QObject):
    ui: Ui_OFDSDedupToolDialog

    def __init__(self, ui: Ui_OFDSDedupToolDialog):
        self.ui = ui

    def onStartButton(self, state: ToolState) -> ToolState: ...
    def onNextButton(self, state: ToolState) -> ToolState: ...
    def onPrevButton(self, state: ToolState) -> ToolState: ...
    def onSameButton(self, state: ToolState) -> ToolState: ...
    def onNotSameButton(self, state: ToolState) -> ToolState: ...
