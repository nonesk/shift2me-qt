#!/usr/bin/env python3
import sys

from PyQt5.QtWidgets import QMainWindow, QApplication, QAction, qApp
from PyQt5.QtGui import QIcon, QPainter
from PyQt5.QtChart import QBarSet, QBarSeries, QChart, QBarCategoryAxis
from PyQt5 import QtCore

from .ui.ui_mainwindow import Ui_MainWindow
from package.dialogs.SetupDialog import SetupDialog

import qtawesome as qta 

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

        self.barchart()

    def setup(self, event):
        setupDialog = SetupDialog()
        setupDialog.setModal(True)
        setupDialog.exec()

    def patch_ui(self):
        self.ui.tabs.setTabIcon(0, qta.icon('fa.bar-chart'))
        self.ui.tabs.setTabIcon(2, qta.icon('fa.flask'))

    def barchart(self):
        barset = QBarSet("Patate")
        for val in list(range(200)):
            barset << val 
        series = QBarSeries()
        series.append(barset)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("kanar")
        chart.setAnimationOptions(QChart.SeriesAnimations)

        categories = list(str(val) for val in range(200))

        axis = QBarCategoryAxis()
        axis.append(categories)

        chart.createDefaultAxes()
        chart.setAxisX(axis, series)

        chart.legend().setVisible(True)
        chart.legend().setAlignment(QtCore.Qt.AlignBottom)

        self.ui.widget_2.setChart(chart)
        self.ui.widget_2.setRenderHint(QPainter.Antialiasing)


def run():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


