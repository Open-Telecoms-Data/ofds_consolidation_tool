from typing import List, cast

import logging
from qgis.core import QgsProject, QgsMapLayer, QgsVectorLayer, QgsMapLayerType

from .model.consolidation import NetworkNodesConsolidator

from ..gui import Ui_OFDSDedupToolDialog
from .model.network import Network
from .viewmodel.state import (
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
            # TODO: test that each layer is a OFDS layer first? maybe display all but
            #        disable non-OFDS layers?
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

            # TODO: Find the nodes to compare
            # TODO: Do this in a background thread, with an intermediary state?

            return ToolNodeComparisonState(
                networks=(networkA, networkB),
                nodes_consolidator=NetworkNodesConsolidator(
                    networkA,
                    networkB,
                    merge_above=self.ui.autoThresholdSpinBox.value(),
                    ask_above=self.ui.askThresholdSpinBox.value(),
                ),
            )

        else:
            raise ControllerInvalidState

    def onNextButton(self, state: ToolState) -> ToolState:
        if isinstance(state, ToolNodeComparisonState):
            state.gotoNextComparison()
            return state

        else:
            raise ControllerInvalidState

    def onPrevButton(self, state: ToolState) -> ToolState:
        if isinstance(state, ToolNodeComparisonState):
            state.gotoPrevComparison()
            return state

        else:
            raise ControllerInvalidState

    def onSameButton(self, state: ToolState) -> ToolState:
        if isinstance(state, ToolNodeComparisonState):
            if state.setOutcomeConsolidate():
                state.gotoNextComparison()
            return state

        else:
            raise ControllerInvalidState

    def onNotSameButton(self, state: ToolState) -> ToolState:
        if isinstance(state, ToolNodeComparisonState):
            state.setOutcomeDontConsolidate()
            state.gotoNextComparison()
            return state

        else:
            raise ControllerInvalidState

    def onFinishedButton(self, state: ToolState) -> ToolState:
        if isinstance(state, ToolNodeComparisonState):
            if not state.all_compared:
                raise ControllerInvalidState
            return state.finish()

            # return ToolSpanComparisonState(newNetworks, ...)  # TODO
        elif isinstance(state, ToolSpanComparisonState):
            raise NotImplementedError  # TODO

        else:
            raise ControllerInvalidState
