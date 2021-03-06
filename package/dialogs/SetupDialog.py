import qtawesome as qta
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot as Slot
from PyQt5.QtCore import QDir, Qt

from package.delegates.SpinBoxDelegate import SpinBoxDelegate
# from qtpandas.models.DataFrameModel import DataFrameModel
# from qtpandas.views.DataTableView import DataTableWidget
#from qtpandas.models.SupportedDtypes import SupportedDtypes
from package.models.DataFrameModel import DataFrameModel
from package.ui.ui_setupdialog import Ui_Dialog
from package.widgets.AtomComboWidget import AtomComboWidget


class SetupDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.patch_ui()

        self.dirModel = QtWidgets.QFileSystemModel(self)
        self.dirModel.setFilter(QDir.Files)
        self.dirModel.setNameFilters(['*.list'])
        self.dirModel.setNameFilterDisables(False)
        self.dirModel.directoryLoaded.connect(self.auto_select_first)
        self.ui.fileListView.setModel(self.dirModel)

        self.fileModel = DataFrameModel(self)
        self.ui.filePreview.setModel(self.fileModel)
        #self.delegate = SpinBoxDelegate()
        #self.ui.filePreview.setItemDelegate(self.delegate)

        self.atomCombo = [
            self.ui.residueColumn,
            self.ui.protonColumn,
            self.ui.nitrogenColumn
            ]
            
        self.ui.headerCheckbox.stateChanged.connect(self.reload_preview)
        print(QDir.currentPath())
        self.setwd(QDir.currentPath())

    #     self.comboValues = [combo.currentIndex for combo in self.atomCombo]

    #     for combo in self.atomCombo:
    #         combo.currentIndexChanged.connect(self.comboChange)
        
    # @pyqtSlot(int)
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
        useHeaders = 'infer' if self.ui.headerCheckbox.isChecked() else None
        self.fileModel.load_csv(filePath = self.dirModel.filePath(modelIndex),  header = useHeaders)
        if useHeaders:
            options = self.fileModel.df.columns.tolist()
        else:
            options = [ "Col {}".format(idx) for idx in range(len(self.fileModel.df.columns))]
        self.update_options(options)
        print("kanar", self.fileModel.df.columns.tolist())

        
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
        self.ui.editProtocoleBtn.setIcon(qta.icon('fa.cogs'))

    def toggleUI(self, toggle = True):
        self.ui.fileListView.setEnabled(toggle)
        for combo in self.atomCombo:
            combo.setEnabled(toggle)
        self.ui.filePreview.setEnabled(toggle)
        self.ui.headerCheckbox.setEnabled(toggle)
