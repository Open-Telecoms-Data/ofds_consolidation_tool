# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'gui.ui'
#
# Created by: PyQt5 UI code generator 5.15.10
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_OFDSDedupToolDialog(object):
    def setupUi(self, OFDSDedupToolDialog):
        OFDSDedupToolDialog.setObjectName("OFDSDedupToolDialog")
        OFDSDedupToolDialog.resize(947, 965)
        OFDSDedupToolDialog.setSizeGripEnabled(False)
        self.verticalLayout = QtWidgets.QVBoxLayout(OFDSDedupToolDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.tabWidget = QtWidgets.QTabWidget(OFDSDedupToolDialog)
        self.tabWidget.setUsesScrollButtons(False)
        self.tabWidget.setObjectName("tabWidget")
        self.tabSelectInput = QtWidgets.QWidget()
        self.tabSelectInput.setObjectName("tabSelectInput")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.tabSelectInput)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.startButton = QtWidgets.QPushButton(self.tabSelectInput)
        self.startButton.setObjectName("startButton")
        self.gridLayout_3.addWidget(self.startButton, 6, 1, 1, 1)
        self.inputSelectionLabel = QtWidgets.QLabel(self.tabSelectInput)
        self.inputSelectionLabel.setObjectName("inputSelectionLabel")
        self.gridLayout_3.addWidget(self.inputSelectionLabel, 0, 0, 1, 1)
        self.selectFormsLayout = QtWidgets.QHBoxLayout()
        self.selectFormsLayout.setObjectName("selectFormsLayout")
        self.groupBoxA = QtWidgets.QGroupBox(self.tabSelectInput)
        self.groupBoxA.setObjectName("groupBoxA")
        self.selectFormA = QtWidgets.QFormLayout(self.groupBoxA)
        self.selectFormA.setObjectName("selectFormA")
        self.nodesLabelA = QtWidgets.QLabel(self.groupBoxA)
        self.nodesLabelA.setObjectName("nodesLabelA")
        self.selectFormA.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.nodesLabelA)
        self.nodesComboBoxA = QtWidgets.QComboBox(self.groupBoxA)
        self.nodesComboBoxA.setObjectName("nodesComboBoxA")
        self.selectFormA.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.nodesComboBoxA)
        self.spansLabelA = QtWidgets.QLabel(self.groupBoxA)
        self.spansLabelA.setObjectName("spansLabelA")
        self.selectFormA.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.spansLabelA)
        self.spansComboBoxA = QtWidgets.QComboBox(self.groupBoxA)
        self.spansComboBoxA.setObjectName("spansComboBoxA")
        self.selectFormA.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.spansComboBoxA)
        self.networkComboBoxA = QtWidgets.QComboBox(self.groupBoxA)
        self.networkComboBoxA.setObjectName("networkComboBoxA")
        self.selectFormA.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.networkComboBoxA)
        self.networkLabelA = QtWidgets.QLabel(self.groupBoxA)
        self.networkLabelA.setObjectName("networkLabelA")
        self.selectFormA.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.networkLabelA)
        self.selectFormsLayout.addWidget(self.groupBoxA)
        self.groupBoxB = QtWidgets.QGroupBox(self.tabSelectInput)
        self.groupBoxB.setObjectName("groupBoxB")
        self.selectFormB = QtWidgets.QFormLayout(self.groupBoxB)
        self.selectFormB.setObjectName("selectFormB")
        self.nodesLabelB = QtWidgets.QLabel(self.groupBoxB)
        self.nodesLabelB.setObjectName("nodesLabelB")
        self.selectFormB.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.nodesLabelB)
        self.nodesComboBoxB = QtWidgets.QComboBox(self.groupBoxB)
        self.nodesComboBoxB.setObjectName("nodesComboBoxB")
        self.selectFormB.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.nodesComboBoxB)
        self.spansLabelB = QtWidgets.QLabel(self.groupBoxB)
        self.spansLabelB.setObjectName("spansLabelB")
        self.selectFormB.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.spansLabelB)
        self.spansComboBoxB = QtWidgets.QComboBox(self.groupBoxB)
        self.spansComboBoxB.setObjectName("spansComboBoxB")
        self.selectFormB.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.spansComboBoxB)
        self.networkComboBoxB = QtWidgets.QComboBox(self.groupBoxB)
        self.networkComboBoxB.setObjectName("networkComboBoxB")
        self.selectFormB.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.networkComboBoxB)
        self.networkLabelB = QtWidgets.QLabel(self.groupBoxB)
        self.networkLabelB.setObjectName("networkLabelB")
        self.selectFormB.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.networkLabelB)
        self.selectFormsLayout.addWidget(self.groupBoxB)
        self.gridLayout_3.addLayout(self.selectFormsLayout, 1, 0, 1, 2)
        self.settingsFormLayout = QtWidgets.QFormLayout()
        self.settingsFormLayout.setObjectName("settingsFormLayout")
        self.autoThresholdLabel = QtWidgets.QLabel(self.tabSelectInput)
        self.autoThresholdLabel.setObjectName("autoThresholdLabel")
        self.settingsFormLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.autoThresholdLabel)
        self.autoThresholdSpinBox = QtWidgets.QSpinBox(self.tabSelectInput)
        self.autoThresholdSpinBox.setMaximum(100)
        self.autoThresholdSpinBox.setProperty("value", 100)
        self.autoThresholdSpinBox.setObjectName("autoThresholdSpinBox")
        self.settingsFormLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.autoThresholdSpinBox)
        self.askThresholdLabel = QtWidgets.QLabel(self.tabSelectInput)
        self.askThresholdLabel.setObjectName("askThresholdLabel")
        self.settingsFormLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.askThresholdLabel)
        self.askThresholdSpinBox = QtWidgets.QSpinBox(self.tabSelectInput)
        self.askThresholdSpinBox.setMaximum(100)
        self.askThresholdSpinBox.setProperty("value", 0)
        self.askThresholdSpinBox.setObjectName("askThresholdSpinBox")
        self.settingsFormLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.askThresholdSpinBox)
        self.label = QtWidgets.QLabel(self.tabSelectInput)
        self.label.setObjectName("label")
        self.settingsFormLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.label)
        self.nodesMatchRadiusSpinBox = QtWidgets.QSpinBox(self.tabSelectInput)
        self.nodesMatchRadiusSpinBox.setMinimum(1)
        self.nodesMatchRadiusSpinBox.setMaximum(200)
        self.nodesMatchRadiusSpinBox.setProperty("value", 10)
        self.nodesMatchRadiusSpinBox.setObjectName("nodesMatchRadiusSpinBox")
        self.settingsFormLayout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.nodesMatchRadiusSpinBox)
        self.gridLayout_3.addLayout(self.settingsFormLayout, 4, 0, 1, 1)
        self.settingsLabel = QtWidgets.QLabel(self.tabSelectInput)
        self.settingsLabel.setObjectName("settingsLabel")
        self.gridLayout_3.addWidget(self.settingsLabel, 3, 0, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout_3.addItem(spacerItem, 5, 1, 1, 1)
        self.tabWidget.addTab(self.tabSelectInput, "")
        self.tabConsolidateNodes = QtWidgets.QWidget()
        self.tabConsolidateNodes.setObjectName("tabConsolidateNodes")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.tabConsolidateNodes)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.nodesProgressLayout = QtWidgets.QHBoxLayout()
        self.nodesProgressLayout.setObjectName("nodesProgressLayout")
        self.comparisonLabel = QtWidgets.QLabel(self.tabConsolidateNodes)
        self.comparisonLabel.setObjectName("comparisonLabel")
        self.nodesProgressLayout.addWidget(self.comparisonLabel)
        self.comparisonProgressBar = QtWidgets.QProgressBar(self.tabConsolidateNodes)
        self.comparisonProgressBar.setMinimum(0)
        self.comparisonProgressBar.setMaximum(1)
        self.comparisonProgressBar.setProperty("value", 0)
        self.comparisonProgressBar.setObjectName("comparisonProgressBar")
        self.nodesProgressLayout.addWidget(self.comparisonProgressBar)
        self.finishedNodesButton = QtWidgets.QPushButton(self.tabConsolidateNodes)
        self.finishedNodesButton.setObjectName("finishedNodesButton")
        self.nodesProgressLayout.addWidget(self.finishedNodesButton)
        self.verticalLayout_2.addLayout(self.nodesProgressLayout)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_3 = QtWidgets.QLabel(self.tabConsolidateNodes)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout.addWidget(self.label_3)
        self.label_2 = QtWidgets.QLabel(self.tabConsolidateNodes)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout.addWidget(self.label_2)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.mapsLayout = QtWidgets.QHBoxLayout()
        self.mapsLayout.setObjectName("mapsLayout")
        self.mapA = gui.QgsMapCanvas(self.tabConsolidateNodes)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.mapA.sizePolicy().hasHeightForWidth())
        self.mapA.setSizePolicy(sizePolicy)
        self.mapA.setMinimumSize(QtCore.QSize(0, 300))
        self.mapA.setObjectName("mapA")
        self.mapsLayout.addWidget(self.mapA)
        self.mapB = gui.QgsMapCanvas(self.tabConsolidateNodes)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.mapB.sizePolicy().hasHeightForWidth())
        self.mapB.setSizePolicy(sizePolicy)
        self.mapB.setMinimumSize(QtCore.QSize(0, 300))
        self.mapB.setObjectName("mapB")
        self.mapsLayout.addWidget(self.mapB)
        self.verticalLayout_2.addLayout(self.mapsLayout)
        self.infoPanel = QtWidgets.QTextEdit(self.tabConsolidateNodes)
        self.infoPanel.setUndoRedoEnabled(False)
        self.infoPanel.setReadOnly(True)
        self.infoPanel.setObjectName("infoPanel")
        self.verticalLayout_2.addWidget(self.infoPanel)
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.sameNodesButton = QtWidgets.QPushButton(self.tabConsolidateNodes)
        self.sameNodesButton.setObjectName("sameNodesButton")
        self.gridLayout.addWidget(self.sameNodesButton, 0, 1, 1, 1)
        self.nextNodesButton = QtWidgets.QPushButton(self.tabConsolidateNodes)
        self.nextNodesButton.setObjectName("nextNodesButton")
        self.gridLayout.addWidget(self.nextNodesButton, 0, 4, 1, 1)
        self.prevNodesButton = QtWidgets.QPushButton(self.tabConsolidateNodes)
        self.prevNodesButton.setObjectName("prevNodesButton")
        self.gridLayout.addWidget(self.prevNodesButton, 0, 0, 1, 1)
        self.notSameNodesButton = QtWidgets.QPushButton(self.tabConsolidateNodes)
        self.notSameNodesButton.setObjectName("notSameNodesButton")
        self.gridLayout.addWidget(self.notSameNodesButton, 0, 2, 1, 1)
        self.verticalLayout_2.addLayout(self.gridLayout)
        self.tabWidget.addTab(self.tabConsolidateNodes, "")
        self.tabConsolidateSpans = QtWidgets.QWidget()
        self.tabConsolidateSpans.setObjectName("tabConsolidateSpans")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.tabConsolidateSpans)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.spansProgressLayout = QtWidgets.QHBoxLayout()
        self.spansProgressLayout.setObjectName("spansProgressLayout")
        self.spansComparisonLabel = QtWidgets.QLabel(self.tabConsolidateSpans)
        self.spansComparisonLabel.setObjectName("spansComparisonLabel")
        self.spansProgressLayout.addWidget(self.spansComparisonLabel)
        self.spansComparisonProgressBar = QtWidgets.QProgressBar(self.tabConsolidateSpans)
        self.spansComparisonProgressBar.setMinimum(0)
        self.spansComparisonProgressBar.setMaximum(1)
        self.spansComparisonProgressBar.setProperty("value", 0)
        self.spansComparisonProgressBar.setObjectName("spansComparisonProgressBar")
        self.spansProgressLayout.addWidget(self.spansComparisonProgressBar)
        self.spansFinishedButton = QtWidgets.QPushButton(self.tabConsolidateSpans)
        self.spansFinishedButton.setObjectName("spansFinishedButton")
        self.spansProgressLayout.addWidget(self.spansFinishedButton)
        self.verticalLayout_3.addLayout(self.spansProgressLayout)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_4 = QtWidgets.QLabel(self.tabConsolidateSpans)
        self.label_4.setObjectName("label_4")
        self.horizontalLayout_2.addWidget(self.label_4)
        self.label_5 = QtWidgets.QLabel(self.tabConsolidateSpans)
        self.label_5.setObjectName("label_5")
        self.horizontalLayout_2.addWidget(self.label_5)
        self.verticalLayout_3.addLayout(self.horizontalLayout_2)
        self.spansMapsLayout = QtWidgets.QHBoxLayout()
        self.spansMapsLayout.setObjectName("spansMapsLayout")
        self.spansMapA = gui.QgsMapCanvas(self.tabConsolidateSpans)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.spansMapA.sizePolicy().hasHeightForWidth())
        self.spansMapA.setSizePolicy(sizePolicy)
        self.spansMapA.setMinimumSize(QtCore.QSize(0, 300))
        self.spansMapA.setObjectName("spansMapA")
        self.spansMapsLayout.addWidget(self.spansMapA)
        self.spansMapB = gui.QgsMapCanvas(self.tabConsolidateSpans)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.spansMapB.sizePolicy().hasHeightForWidth())
        self.spansMapB.setSizePolicy(sizePolicy)
        self.spansMapB.setMinimumSize(QtCore.QSize(0, 300))
        self.spansMapB.setObjectName("spansMapB")
        self.spansMapsLayout.addWidget(self.spansMapB)
        self.verticalLayout_3.addLayout(self.spansMapsLayout)
        self.spansInfoPanel = QtWidgets.QTextEdit(self.tabConsolidateSpans)
        self.spansInfoPanel.setUndoRedoEnabled(False)
        self.spansInfoPanel.setReadOnly(True)
        self.spansInfoPanel.setObjectName("spansInfoPanel")
        self.verticalLayout_3.addWidget(self.spansInfoPanel)
        self.gridLayout_2 = QtWidgets.QGridLayout()
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.spansSameButton = QtWidgets.QPushButton(self.tabConsolidateSpans)
        self.spansSameButton.setObjectName("spansSameButton")
        self.gridLayout_2.addWidget(self.spansSameButton, 0, 1, 1, 1)
        self.spansNextButton = QtWidgets.QPushButton(self.tabConsolidateSpans)
        self.spansNextButton.setObjectName("spansNextButton")
        self.gridLayout_2.addWidget(self.spansNextButton, 0, 4, 1, 1)
        self.spansPrevButton = QtWidgets.QPushButton(self.tabConsolidateSpans)
        self.spansPrevButton.setObjectName("spansPrevButton")
        self.gridLayout_2.addWidget(self.spansPrevButton, 0, 0, 1, 1)
        self.spansNotSameButton = QtWidgets.QPushButton(self.tabConsolidateSpans)
        self.spansNotSameButton.setObjectName("spansNotSameButton")
        self.gridLayout_2.addWidget(self.spansNotSameButton, 0, 2, 1, 1)
        self.verticalLayout_3.addLayout(self.gridLayout_2)
        self.tabWidget.addTab(self.tabConsolidateSpans, "")
        self.tabOutput = QtWidgets.QWidget()
        self.tabOutput.setObjectName("tabOutput")
        self.outputFinishedButton = QtWidgets.QPushButton(self.tabOutput)
        self.outputFinishedButton.setGeometry(QtCore.QRect(750, 820, 103, 36))
        self.outputFinishedButton.setObjectName("outputFinishedButton")
        self.outputMapCanvas = gui.QgsMapCanvas(self.tabOutput)
        self.outputMapCanvas.setGeometry(QtCore.QRect(10, 10, 911, 751))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.outputMapCanvas.sizePolicy().hasHeightForWidth())
        self.outputMapCanvas.setSizePolicy(sizePolicy)
        self.outputMapCanvas.setMinimumSize(QtCore.QSize(0, 300))
        self.outputMapCanvas.setObjectName("outputMapCanvas")
        self.outputSaveNodes = QtWidgets.QPushButton(self.tabOutput)
        self.outputSaveNodes.setGeometry(QtCore.QRect(150, 790, 221, 36))
        self.outputSaveNodes.setObjectName("outputSaveNodes")
        self.outputSaveSpans = QtWidgets.QPushButton(self.tabOutput)
        self.outputSaveSpans.setGeometry(QtCore.QRect(150, 840, 221, 36))
        self.outputSaveSpans.setObjectName("outputSaveSpans")
        self.tabWidget.addTab(self.tabOutput, "")
        self.verticalLayout.addWidget(self.tabWidget)

        self.retranslateUi(OFDSDedupToolDialog)
        self.tabWidget.setCurrentIndex(3)
        self.outputFinishedButton.pressed.connect(OFDSDedupToolDialog.close) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(OFDSDedupToolDialog)

    def retranslateUi(self, OFDSDedupToolDialog):
        _translate = QtCore.QCoreApplication.translate
        OFDSDedupToolDialog.setWindowTitle(_translate("OFDSDedupToolDialog", "OFDS Consolidation Tool"))
        self.startButton.setText(_translate("OFDSDedupToolDialog", "Start"))
        self.inputSelectionLabel.setText(_translate("OFDSDedupToolDialog", "Input Selection"))
        self.groupBoxA.setTitle(_translate("OFDSDedupToolDialog", "Primary Network"))
        self.nodesLabelA.setText(_translate("OFDSDedupToolDialog", "Nodes"))
        self.spansLabelA.setText(_translate("OFDSDedupToolDialog", "Spans"))
        self.networkLabelA.setText(_translate("OFDSDedupToolDialog", "Network"))
        self.groupBoxB.setTitle(_translate("OFDSDedupToolDialog", "Secondary Network"))
        self.nodesLabelB.setText(_translate("OFDSDedupToolDialog", "Nodes"))
        self.spansLabelB.setText(_translate("OFDSDedupToolDialog", "Spans"))
        self.networkLabelB.setText(_translate("OFDSDedupToolDialog", "Network"))
        self.autoThresholdLabel.setText(_translate("OFDSDedupToolDialog", "Auto Consolidate Above (%)"))
        self.askThresholdLabel.setText(_translate("OFDSDedupToolDialog", "Ask Above (%)"))
        self.label.setText(_translate("OFDSDedupToolDialog", "Node Match Radius (km)"))
        self.settingsLabel.setText(_translate("OFDSDedupToolDialog", "Settings"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabSelectInput), _translate("OFDSDedupToolDialog", "Select Input"))
        self.comparisonLabel.setText(_translate("OFDSDedupToolDialog", "Node Comparisons"))
        self.comparisonProgressBar.setFormat(_translate("OFDSDedupToolDialog", "%v of %m"))
        self.finishedNodesButton.setText(_translate("OFDSDedupToolDialog", "Finish"))
        self.label_3.setText(_translate("OFDSDedupToolDialog", "Primary Node"))
        self.label_2.setText(_translate("OFDSDedupToolDialog", "Secondary Node"))
        self.sameNodesButton.setText(_translate("OFDSDedupToolDialog", "Consolidate"))
        self.nextNodesButton.setText(_translate("OFDSDedupToolDialog", "Next >"))
        self.prevNodesButton.setText(_translate("OFDSDedupToolDialog", "< Previous"))
        self.notSameNodesButton.setText(_translate("OFDSDedupToolDialog", "Keep Both"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabConsolidateNodes), _translate("OFDSDedupToolDialog", "Consolidate Nodes"))
        self.spansComparisonLabel.setText(_translate("OFDSDedupToolDialog", "Span Comparisons"))
        self.spansComparisonProgressBar.setFormat(_translate("OFDSDedupToolDialog", "%v of %m"))
        self.spansFinishedButton.setText(_translate("OFDSDedupToolDialog", "Finish"))
        self.label_4.setText(_translate("OFDSDedupToolDialog", "Span A"))
        self.label_5.setText(_translate("OFDSDedupToolDialog", "Span B"))
        self.spansSameButton.setText(_translate("OFDSDedupToolDialog", "Consolidate"))
        self.spansNextButton.setText(_translate("OFDSDedupToolDialog", "Next >"))
        self.spansPrevButton.setText(_translate("OFDSDedupToolDialog", "< Previous"))
        self.spansNotSameButton.setText(_translate("OFDSDedupToolDialog", "Keep Both"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabConsolidateSpans), _translate("OFDSDedupToolDialog", "Consolidate Spans"))
        self.outputFinishedButton.setText(_translate("OFDSDedupToolDialog", "Close"))
        self.outputSaveNodes.setText(_translate("OFDSDedupToolDialog", "Save Nodes GeoJSON"))
        self.outputSaveSpans.setText(_translate("OFDSDedupToolDialog", "Save Spans GeoJSON"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabOutput), _translate("OFDSDedupToolDialog", "Output"))
from qgis import gui
