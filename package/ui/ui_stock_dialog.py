# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'designer/stock_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(400, 300)
        self.horizontalLayout = QtWidgets.QHBoxLayout(Dialog)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.listView = QtWidgets.QListView(Dialog)
        self.listView.setObjectName("listView")
        self.gridLayout.addWidget(self.listView, 12, 0, 1, 1)
        self.formGroupBox = QtWidgets.QGroupBox(Dialog)
        self.formGroupBox.setObjectName("formGroupBox")
        self.formLayout = QtWidgets.QFormLayout(self.formGroupBox)
        self.formLayout.setObjectName("formLayout")
        self.nameLabel = QtWidgets.QLabel(self.formGroupBox)
        self.nameLabel.setObjectName("nameLabel")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.nameLabel)
        self.nameLineEdit = QtWidgets.QLineEdit(self.formGroupBox)
        self.nameLineEdit.setObjectName("nameLineEdit")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.nameLineEdit)
        self.concentrationLabel = QtWidgets.QLabel(self.formGroupBox)
        self.concentrationLabel.setObjectName("concentrationLabel")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.concentrationLabel)
        self.concentrationDoubleSpinBox = QtWidgets.QDoubleSpinBox(self.formGroupBox)
        self.concentrationDoubleSpinBox.setMinimum(1.0)
        self.concentrationDoubleSpinBox.setObjectName("concentrationDoubleSpinBox")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.concentrationDoubleSpinBox)
        self.unitLabel = QtWidgets.QLabel(self.formGroupBox)
        self.unitLabel.setObjectName("unitLabel")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.unitLabel)
        self.unitComboBox = QtWidgets.QComboBox(self.formGroupBox)
        self.unitComboBox.setObjectName("unitComboBox")
        self.unitComboBox.addItem("")
        self.unitComboBox.addItem("")
        self.unitComboBox.addItem("")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.unitComboBox)
        self.gridLayout.addWidget(self.formGroupBox, 0, 0, 1, 1)
        self.horizontalLayout.addLayout(self.gridLayout)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.addBtn = QtWidgets.QPushButton(Dialog)
        self.addBtn.setObjectName("addBtn")
        self.verticalLayout.addWidget(self.addBtn)
        self.updateBtn = QtWidgets.QPushButton(Dialog)
        self.updateBtn.setObjectName("updateBtn")
        self.verticalLayout.addWidget(self.updateBtn)
        self.deleteBtn = QtWidgets.QPushButton(Dialog)
        self.deleteBtn.setEnabled(False)
        self.deleteBtn.setObjectName("deleteBtn")
        self.verticalLayout.addWidget(self.deleteBtn)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Vertical)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(True)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)
        self.horizontalLayout.addLayout(self.verticalLayout)

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.formGroupBox.setTitle(_translate("Dialog", "Stock Solution Parameters"))
        self.nameLabel.setText(_translate("Dialog", "Molecule"))
        self.concentrationLabel.setText(_translate("Dialog", "Concentration"))
        self.unitLabel.setText(_translate("Dialog", "Unit"))
        self.unitComboBox.setItemText(0, _translate("Dialog", "µM"))
        self.unitComboBox.setItemText(1, _translate("Dialog", "mM"))
        self.unitComboBox.setItemText(2, _translate("Dialog", "M"))
        self.addBtn.setText(_translate("Dialog", "Add"))
        self.updateBtn.setText(_translate("Dialog", "Edit"))
        self.deleteBtn.setText(_translate("Dialog", "Delete"))

