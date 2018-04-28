import sys

import qtawesome as qta
from PyQt5 import QtCore
from PyQt5.QtWidgets import QAction, QApplication, QMainWindow, qApp

from package.controllers.BarChartController import BarChartController
from package.dialogs.SetupDialog import SetupDialog
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
        self.resize(1200, 665)

        
        self.init_controllers()


    def init_controllers(self):
        self.cutoffCtrl = BarChartController(self)

    def setup(self, event):
        setupDialog = SetupDialog()
        setupDialog.setModal(True)
        setupDialog.exec()

    def patch_ui(self):
        self.ui.tabs.setTabIcon(0, qta.icon('fa.bar-chart'))
        self.ui.tabs.setTabIcon(1, qta.icon('fa.flask'))



def run():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()
