#!/usr/bin/env python3
import sys

from PyQt5.QtWidgets import QMainWindow, QApplication, QAction, qApp
from PyQt5.QtGui import QIcon

from .ui.ui_mainwindow import Ui_MainWindow
from package.dialogs.SetupDialog import SetupDialog


class MainWindow(QMainWindow):
    """Shift2Me GUI main window class
    """
    def __init__(self, parent=None):
        super().__init__() # init QWidget main window

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.setWindowTitle("Shift2Me")
        self.setObjectName("MainWindow")
        self.resize(1200, 665)

    def setup(self, event):
        setupDialog = SetupDialog()
        setupDialog.setModal(True)
        setupDialog.exec()

def run():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


