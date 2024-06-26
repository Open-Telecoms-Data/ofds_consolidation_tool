from typing import List, cast

import logging
from qgis.core import QgsProject, QgsMapLayer, QgsVectorLayer, QgsMapLayerType

from .model.settings import Settings

from ..gui import Ui_OFDSDedupToolDialog
from .model.network import Network
from .viewmodel.state import (
    ToolLayerSelectState,
    ToolNodeComparisonState,
    ToolOutputState,
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
            networkA = Network.from_qgs_vectorlayers(
                nodesLayer=self.ui.nodesComboBoxA.currentData(),
                spansLayer=self.ui.spansComboBoxA.currentData(),
            )

            networkB = Network.from_qgs_vectorlayers(
                nodesLayer=self.ui.nodesComboBoxB.currentData(),
                spansLayer=self.ui.spansComboBoxB.currentData(),
            )

            # TODO: Find the nodes to compare
            # TODO: Do this in a background thread, with an intermediary state?

            settings = Settings(
                nodes_merge_threshold=self.ui.autoThresholdSpinBox.value(),
                nodes_ask_threshold=self.ui.askThresholdSpinBox.value(),
                nodes_match_radius_km=float(self.ui.nodesMatchRadiusSpinBox.value()),
            )

            return ToolNodeComparisonState(
                settings=settings,
                networks=(networkA, networkB),
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

    def onSameButton(self, state: ToolState) -> ToolState:
        if isinstance(state, ToolNodeComparisonState) or isinstance(
            state, ToolSpanComparisonState
        ):
            state.setOutcomeConsolidate()
            return state

        else:
            raise ControllerInvalidState

    def onNotSameButton(self, state: ToolState) -> ToolState:
        if isinstance(state, ToolNodeComparisonState) or isinstance(
            state, ToolSpanComparisonState
        ):
            state.setOutcomeDontConsolidate()
            return state

        else:
            raise ControllerInvalidState

    def onFinishedButton(self, state: ToolState) -> ToolState:
        if isinstance(state, ToolNodeComparisonState):
            return state.finish()

        elif isinstance(state, ToolSpanComparisonState):
            return state.finish()

        elif isinstance(state, ToolOutputState):
            # Restart the tool when finished
            return self.onInit()

        else:
            raise ControllerInvalidState

    def onSaveNodesButton(self, state: ToolState) -> ToolState:
        if isinstance(state, ToolOutputState):
            return state.saveNodes()
        else:
            raise ControllerInvalidState

    def onSaveSpansButton(self, state: ToolState) -> ToolState:
        if isinstance(state, ToolOutputState):
            return state.saveSpans()
        else:
            raise ControllerInvalidState
