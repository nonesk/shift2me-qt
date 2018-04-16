# -*- coding: utf-8 -*-


from PyQt5.QtCore import pyqtSlot as Slot
from PyQt5 import QtCore, QtWidgets, QtGui


from package.ui.ui_setupdialog import Ui_Dialog
from package.widgets.AtomComboWidget import AtomComboWidget
import pandas as pd
import functools

import qtawesome as qta

class PandasTableModel(QtCore.QAbstractTableModel):
    def __init__(self, parent=None, *args):
        super().__init__(parent)
        self.df = pd.DataFrame()
        

    def load_csv(self, filePath, header):
        with open(filePath, "r") as fh:
            self.df = pd.read_table(fh, sep='\\s+', header=header)
            self.modelReset.emit()

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.df.index)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self.df.columns.values)

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()

        if orientation == QtCore.Qt.Horizontal:
            try:
                return self.df.columns.tolist()[section]
            except (IndexError, ):
                return QtCore.QVariant()
        elif orientation == QtCore.Qt.Vertical:
            try:
                # return self.df.index.tolist()
                return self.df.index.tolist()[section]
            except (IndexError, ):
                return QtCore.QVariant()

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()

        if not index.isValid():
            return QtCore.QVariant()

        return QtCore.QVariant(str(self.df.ix[index.row(), index.column()]))
    
    def sort(self, column, order):
        colname = self.df.columns.tolist()[column]
        self.layoutAboutToBeChanged.emit()
        self.df.sort_values(colname, ascending= order == QtCore.Qt.AscendingOrder, inplace=True)
        self.df.reset_index(inplace=True, drop=True)
        self.layoutChanged.emit()

class SetupDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.patch_ui()

        self.dirModel = QtWidgets.QFileSystemModel(self)
        self.dirModel.setFilter(QtCore.QDir.Files)
        self.dirModel.setNameFilters(['*.list'])
        self.dirModel.setNameFilterDisables(False)
        self.dirModel.directoryLoaded.connect(self.auto_select_first)
        self.ui.fileListView.setModel(self.dirModel)

        self.fileModel = PandasTableModel()
        self.ui.filePreview.setModel(self.fileModel)

        self.atomCombo = [
            self.ui.residueColumn,
            self.ui.protonColumn,
            self.ui.nitrogenColumn
            ]
            
        self.ui.headerCheckbox.stateChanged.connect(self.reload_preview)
        print(QtCore.QDir.currentPath())
        self.setwd(QtCore.QDir.currentPath())

    #     self.comboValues = [combo.currentIndex for combo in self.atomCombo]

    #     for combo in self.atomCombo:
    #         combo.currentIndexChanged.connect(self.comboChange)
        
    # @QtCore.pyqtSlot(int)
    # def comboChange(self, index):
    #     for comboId, combo in enumerate(self.atomCombo):
    #         if combo.currentIndex == index:
    #             combo.setCurrentIndex(0)


    def update_options(self, options):
        for index, combo in enumerate(self.atomCombo):
            combo.clear()
            for opt in options:
                combo.addItem(opt)
            combo.setCurrentIndex(index)
        self.comboValues = [combo.currentIndex for combo in self.atomCombo]

    def reload_preview(self):
        selected = self.ui.fileListView.selectedIndexes().pop()
        self.load_csv(selected)

    def load_csv(self, modelIndex): 
        print("Dialog caught signal")
        useHeaders = 'infer' if self.ui.headerCheckbox.isChecked() else None
        self.fileModel.load_csv(filePath = self.dirModel.filePath(modelIndex), header = useHeaders)
        if useHeaders:
            options = list(self.fileModel.df.columns.values)
        else:
            options = [ "Col {}".format(idx) for idx in range(len(self.fileModel.df.columns))]
        self.update_options(options)

        
    def browse(self, event):
        directory = QtWidgets.QFileDialog.getExistingDirectory(self, "RMN Data directory")
        print(directory)
        if directory:
            self.setwd(directory)
        return directory

    def setwd(self, directory):
        self.parentIndex = self.dirModel.setRootPath(directory)
        #self.dirModel.setCurrentIndex(self.parentIndex)
        print(self.dirModel.filePath(self.parentIndex))
        self.ui.fileListView.setRootIndex(self.dirModel.index(directory))
        self.ui.cwdLabel.setText(directory)
        self.ui.fileListView.setEnabled(True)
            

    def auto_select_first(self, path):
        print(self.dirModel.rowCount(self.parentIndex))
        if self.dirModel.rowCount(self.parentIndex):
            self.toggleUI(True)
            self.ui.fileListView.setCurrentIndex(
                self.dirModel.index(0,0, 
                    self.dirModel.index(path)
                    )
                )
            self.reload_preview()
        else:
            self.toggleUI(False)

    def patch_ui(self):
        self.ui.editProtocoleBtn.setIcon(qta.icon('fa.flask'))

    def toggleUI(self, toggle = True):
        self.ui.fileListView.setEnabled(toggle)
        for combo in self.atomCombo:
            combo.setEnabled(toggle)
        self.ui.filePreview.setEnabled(toggle)
        self.ui.headerCheckbox.setEnabled(toggle)
        