import sys

import qtawesome as qta
from PyQt5 import QtCore
from PyQt5.QtWidgets import QAction, QApplication, QMainWindow, qApp
from PyQt5.QtGui import QStandardItemModel

from package.controllers.BarChartController import BarChartController
from package.controllers.ProtocoleController import ProtocoleController
from package.dialogs.SetupDialog import SetupDialog
from package.dialogs.StockDialog import StockDialog
from package.ui.ui_mainwindow import Ui_MainWindow


class MainWindow(QMainWindow):
    """Shift2Me GUI main window class
    """
    def __init__(self, parent=None):
        super().__init__() # init QWidget main window

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.patch_ui()

        self.setWindowTitle("Shift2Me")
        self.setObjectName("MainWindow")
        self.resize(1200, 800)

        
        self.init_controllers()

        

        # for i in range(4):
        #     for j in range(2):
        #         index = self.protocoleModel.index(i,j,QtCore.QModelIndex())
        #         self.protocoleModel.setData(index, 0)


    def init_controllers(self):
        self.cutoffCtrl = BarChartController(self)
        self.protocoleCtrl = ProtocoleController(self)

    def setup(self, event):
        setupDialog = SetupDialog()
        setupDialog.setModal(True)
        setupDialog.exec()

    def edit_stock(self, event):
        stockDialog = StockDialog()
        stockDialog.exec()

    def patch_ui(self):
        self.ui.tabs.setTabIcon(0, qta.icon('fa.bar-chart'))
        self.ui.tabs.setTabIcon(1, qta.icon('fa.cogs'))
        self.ui.addStepBtn.setIcon(qta.icon('fa.plus'))
        self.ui.removeStepBtn.setIcon(qta.icon('fa.minus'))
        self.ui.analyteInitialVolume.valueChanged.connect(self.ui.totalInitialVolume.setMinimum)
        self.ui.actionStock_solutions.setIcon(qta.icon('fa.flask'))
        self.ui.manageStockBtn.setIcon(qta.icon('fa.flask'))


def run():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()
