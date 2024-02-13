# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'gui.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_OFDSDedupToolDialog(object):
    def setupUi(self, OFDSDedupToolDialog):
        OFDSDedupToolDialog.setObjectName("OFDSDedupToolDialog")
        OFDSDedupToolDialog.resize(947, 965)
        OFDSDedupToolDialog.setSizeGripEnabled(False)
        self.buttons = QtWidgets.QDialogButtonBox(OFDSDedupToolDialog)
        self.buttons.setGeometry(QtCore.QRect(770, 910, 166, 36))
        self.buttons.setOrientation(QtCore.Qt.Horizontal)
        self.buttons.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttons.setObjectName("buttons")
        self.layoutWidget = QtWidgets.QWidget(OFDSDedupToolDialog)
        self.layoutWidget.setGeometry(QtCore.QRect(6, 6, 931, 122))
        self.layoutWidget.setObjectName("layoutWidget")
        self.selectFormsLayout = QtWidgets.QHBoxLayout(self.layoutWidget)
        self.selectFormsLayout.setContentsMargins(0, 0, 0, 0)
        self.selectFormsLayout.setObjectName("selectFormsLayout")
        self.groupBoxA = QtWidgets.QGroupBox(self.layoutWidget)
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
        self.selectFormsLayout.addWidget(self.groupBoxA)
        self.groupBoxB = QtWidgets.QGroupBox(self.layoutWidget)
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
        self.selectFormsLayout.addWidget(self.groupBoxB)
        self.layoutWidget1 = QtWidgets.QWidget(OFDSDedupToolDialog)
        self.layoutWidget1.setGeometry(QtCore.QRect(10, 170, 921, 281))
        self.layoutWidget1.setObjectName("layoutWidget1")
        self.mapsLayout = QtWidgets.QHBoxLayout(self.layoutWidget1)
        self.mapsLayout.setContentsMargins(0, 0, 0, 0)
        self.mapsLayout.setObjectName("mapsLayout")
        self.mapA = gui.QgsMapCanvas(self.layoutWidget1)
        self.mapA.setObjectName("mapA")
        self.mapsLayout.addWidget(self.mapA)
        self.mapB = gui.QgsMapCanvas(self.layoutWidget1)
        self.mapB.setObjectName("mapB")
        self.mapsLayout.addWidget(self.mapB)
        self.layoutWidget2 = QtWidgets.QWidget(OFDSDedupToolDialog)
        self.layoutWidget2.setGeometry(QtCore.QRect(6, 120, 931, 38))
        self.layoutWidget2.setObjectName("layoutWidget2")
        self.startLayout = QtWidgets.QHBoxLayout(self.layoutWidget2)
        self.startLayout.setContentsMargins(0, 0, 0, 0)
        self.startLayout.setObjectName("startLayout")
        self.startButton = QtWidgets.QPushButton(self.layoutWidget2)
        self.startButton.setMaximumSize(QtCore.QSize(100, 16777215))
        self.startButton.setObjectName("startButton")
        self.startLayout.addWidget(self.startButton)
        self.label = QtWidgets.QLabel(self.layoutWidget2)
        self.label.setObjectName("label")
        self.startLayout.addWidget(self.label)
        self.nodesProgressBar = QtWidgets.QProgressBar(self.layoutWidget2)
        self.nodesProgressBar.setMinimum(0)
        self.nodesProgressBar.setMaximum(1)
        self.nodesProgressBar.setProperty("value", 0)
        self.nodesProgressBar.setObjectName("nodesProgressBar")
        self.startLayout.addWidget(self.nodesProgressBar)
        self.label_2 = QtWidgets.QLabel(self.layoutWidget2)
        self.label_2.setObjectName("label_2")
        self.startLayout.addWidget(self.label_2)
        self.spansProgressBar = QtWidgets.QProgressBar(self.layoutWidget2)
        self.spansProgressBar.setMaximum(1)
        self.spansProgressBar.setProperty("value", 0)
        self.spansProgressBar.setObjectName("spansProgressBar")
        self.startLayout.addWidget(self.spansProgressBar)
        self.sameButton = QtWidgets.QPushButton(OFDSDedupToolDialog)
        self.sameButton.setGeometry(QtCore.QRect(400, 790, 141, 36))
        self.sameButton.setObjectName("sameButton")
        self.notSameButton = QtWidgets.QPushButton(OFDSDedupToolDialog)
        self.notSameButton.setGeometry(QtCore.QRect(400, 830, 141, 36))
        self.notSameButton.setObjectName("notSameButton")
        self.infoPanelA = QtWidgets.QPlainTextEdit(OFDSDedupToolDialog)
        self.infoPanelA.setGeometry(QtCore.QRect(10, 460, 461, 301))
        self.infoPanelA.setUndoRedoEnabled(False)
        self.infoPanelA.setReadOnly(True)
        self.infoPanelA.setObjectName("infoPanelA")
        self.infoPanelB = QtWidgets.QPlainTextEdit(OFDSDedupToolDialog)
        self.infoPanelB.setGeometry(QtCore.QRect(470, 460, 461, 301))
        self.infoPanelB.setUndoRedoEnabled(False)
        self.infoPanelB.setReadOnly(True)
        self.infoPanelB.setObjectName("infoPanelB")
        self.layoutWidget.raise_()
        self.buttons.raise_()
        self.layoutWidget.raise_()
        self.layoutWidget.raise_()
        self.sameButton.raise_()
        self.notSameButton.raise_()
        self.infoPanelA.raise_()
        self.infoPanelB.raise_()

        self.retranslateUi(OFDSDedupToolDialog)
        self.buttons.accepted.connect(OFDSDedupToolDialog.accept) # type: ignore
        self.buttons.rejected.connect(OFDSDedupToolDialog.reject) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(OFDSDedupToolDialog)

    def retranslateUi(self, OFDSDedupToolDialog):
        _translate = QtCore.QCoreApplication.translate
        OFDSDedupToolDialog.setWindowTitle(_translate("OFDSDedupToolDialog", "OFDS Dedup Tool"))
        self.groupBoxA.setTitle(_translate("OFDSDedupToolDialog", "Network A"))
        self.nodesLabelA.setText(_translate("OFDSDedupToolDialog", "Nodes"))
        self.spansLabelA.setText(_translate("OFDSDedupToolDialog", "Spans"))
        self.groupBoxB.setTitle(_translate("OFDSDedupToolDialog", "Network B"))
        self.nodesLabelB.setText(_translate("OFDSDedupToolDialog", "Nodes"))
        self.spansLabelB.setText(_translate("OFDSDedupToolDialog", "Spans"))
        self.startButton.setText(_translate("OFDSDedupToolDialog", "Start"))
        self.label.setText(_translate("OFDSDedupToolDialog", "Nodes"))
        self.nodesProgressBar.setFormat(_translate("OFDSDedupToolDialog", "%v of %m"))
        self.label_2.setText(_translate("OFDSDedupToolDialog", "Spans"))
        self.spansProgressBar.setFormat(_translate("OFDSDedupToolDialog", "%v of %m"))
        self.sameButton.setText(_translate("OFDSDedupToolDialog", "Equivelant"))
        self.notSameButton.setText(_translate("OFDSDedupToolDialog", "Not Equivelant"))
from qgis import gui
