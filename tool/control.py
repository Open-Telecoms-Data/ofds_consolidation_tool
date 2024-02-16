from typing import List, cast

import logging
from qgis.core import QgsProject, QgsMapLayer, QgsVectorLayer, QgsMapLayerType

from ..comparisons import compareNodes, NodeComparison
from ..gui import Ui_OFDSDedupToolDialog
from ..models import Network
from .state import (
    ToolLayerSelectState,
    ToolNodeComparisonState,
    ToolSpanComparisonState,
    ToolState,
)

logger = logging.getLogger(__name__)

# The controller is responsible for acceping input from the UI (i.e. button clicks)
# and then translating that into state updates.


class ControllerInvalidState(Exception):
    pass


class ToolController:
    project: QgsProject
    ui: Ui_OFDSDedupToolDialog

    def __init__(self, project: QgsProject, ui: Ui_OFDSDedupToolDialog):
        self.project = project
        self.ui = ui

    def onInit(self) -> ToolState:
        """
        Initialise the start state ready for selecting layers.
        """
        # Find all the layers the user has loaded
        allLayers: List[QgsMapLayer] = self.project.mapLayers(validOnly=True).values()

        # Filter the layers that the tool can accept
        selectableLayers: List[QgsVectorLayer] = list()

        for layer in allLayers:
            # only vector layers can be valid OFDS layers
            # TODO: test that each layer is a OFDS layer first? maybe display all but disable non-OFDS layers?
            if layer.type() == QgsMapLayerType.VectorLayer:
                selectableLayers.append(cast(QgsVectorLayer, layer))

        return ToolLayerSelectState(selectableLayers)

    def onStartButton(self, state: ToolState) -> ToolState:
        """
        When the start button is pressed, transition to comparing nodes.
        """
        if isinstance(state, ToolLayerSelectState):
            # Gather layers to use
            networkA = Network(
                nodesLayer=self.ui.nodesComboBoxA.currentData(),
                spansLayer=self.ui.spansComboBoxA.currentData(),
            )

            networkB = Network(
                nodesLayer=self.ui.nodesComboBoxB.currentData(),
                spansLayer=self.ui.spansComboBoxB.currentData(),
            )

            # Find the nodes to compare
            # TODO: Do this in a background thread, with an intermediary state?
            nodeComparisons: List[NodeComparison] = list(
                compareNodes(networkA, networkB)
            )

            return ToolNodeComparisonState(
                networks=(networkA, networkB), comparisons=nodeComparisons
            )

        else:
            raise ControllerInvalidState

    def onNextButton(self, state: ToolState) -> ToolState:
        if isinstance(state, ToolNodeComparisonState) or isinstance(
            state, ToolSpanComparisonState
        ):
            state.gotoNextComparison()
            return state

        else:
            raise ControllerInvalidState

    def onPrevButton(self, state: ToolState) -> ToolState:
        if isinstance(state, ToolNodeComparisonState) or isinstance(
            state, ToolSpanComparisonState
        ):
            state.gotoPrevComparison()
            return state

        else:
            raise ControllerInvalidState

    def onSameButton(self, state: ToolState) -> ToolState: ...
    def onNotSameButton(self, state: ToolState) -> ToolState: ...
