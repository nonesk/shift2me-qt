# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'setupdialog.ui'
#
# Created by: PyQt5 UI code generator 5.10
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        Dialog.resize(600, 500)
        Dialog.setAutoFillBackground(False)
        Dialog.setSizeGripEnabled(False)
        Dialog.setModal(True)
        self.gridLayout = QtWidgets.QGridLayout(Dialog)
        self.gridLayout.setObjectName("gridLayout")
        self.splitter = QtWidgets.QSplitter(Dialog)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.groupBox = QtWidgets.QGroupBox(self.splitter)
        self.groupBox.setObjectName("groupBox")
        self.formLayout = QtWidgets.QFormLayout(self.groupBox)
        self.formLayout.setObjectName("formLayout")
        self.toolButton = QtWidgets.QToolButton(self.groupBox)
        self.toolButton.setText("")
        icon = QtGui.QIcon.fromTheme("folder")
        self.toolButton.setIcon(icon)
        self.toolButton.setObjectName("toolButton")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.toolButton)
        self.cwdLabel = QtWidgets.QLabel(self.groupBox)
        self.cwdLabel.setObjectName("cwdLabel")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.cwdLabel)
        self.fileListView = QtWidgets.QListView(self.splitter)
        self.fileListView.setEnabled(False)
        self.fileListView.setDragEnabled(True)
        self.fileListView.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.fileListView.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.fileListView.setAlternatingRowColors(True)
        self.fileListView.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.fileListView.setMovement(QtWidgets.QListView.Snap)
        self.fileListView.setObjectName("fileListView")
        self.gridLayout.addWidget(self.splitter, 0, 0, 1, 1)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 1, 0, 1, 1)

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)
        self.toolButton.clicked.connect(Dialog.setwd)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Setup new experiment"))
        self.groupBox.setTitle(_translate("Dialog", "Set working directory"))
        self.cwdLabel.setText(_translate("Dialog", "TextLabel"))

