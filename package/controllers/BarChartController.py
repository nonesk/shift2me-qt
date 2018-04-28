"""A controller to handle UI interactions on chemical shifts barchart
"""


import numpy as np
from PyQt5 import QtCore
from PyQt5.QtChart import (QBarCategoryAxis, QBarSeries, QBarSet, QChart,
                           QLineSeries, QStackedBarSeries,)
from PyQt5.QtCore import QObject, pyqtSlot
from PyQt5.QtGui import QBrush, QColor, QFont, QIcon, QPainter, QPen


class BarChartController(QObject):

    def __init__(self, window, titration = None):
        super().__init__()

        self.parent = window

        self.slider = window.ui.cutoffSlider
        self.floatbox = window.ui.cutoffSpinBox
        self.stepSlider = window.ui.stepSlider
        self.chartview = window.ui.chartview

        self.slider.valueChanged.connect(self.set_cutoff)
        self.stepSlider.valueChanged.connect(self.plot)
        self.floatbox.valueChanged.connect(self.set_cutoff)

        self.init_chart()
        self.set_cutoff(50)

    @pyqtSlot("int")
    @pyqtSlot("double")
    def set_cutoff(self, cutoff):
        sender = self.sender()
        if (sender == self.slider):
            self.floatbox.setValue(cutoff)
        elif (sender == self.floatbox):
            self.slider.setValue(cutoff)
        else:
            self.floatbox.setValue(cutoff)
            self.slider.setValue(cutoff)
        self.move_line(cutoff)

        for index in range(100):
            if self.barset.at(index) >= cutoff or (self.selected.at(index) < cutoff and self.selected.at(index) > 0):
                self.switch_bar(index)
    
    def switch_bar(self, index):
        value = self.barset.at(index)
        self.barset.replace(index, self.selected.at(index))
        self.selected.replace(index, value)

    @pyqtSlot("int")
    def plot(self, value = None):
        
        for index, val in enumerate(np.random.randint(0, 100, 100)):
            
            if val > self.floatbox.value():
                self.selected.replace(index, val)
                self.barset.replace(index, 0)
            else:
                self.barset.replace(index, val)
                self.selected.replace(index, 0)


    def move_line(self, yVal):
        #print(yVal)
        #print(self.sender())
        self.lineSeries.replace(0, QtCore.QPoint(0, yVal))
        self.lineSeries.replace(1, QtCore.QPoint(100, yVal))

    @pyqtSlot("bool", "int")
    def bar_info(self, status, index):
        if not status:
            self.parent.statusBar().clearMessage()
        else:
            value = max(self.selected.at(index), self.barset.at(index))
            self.parent.statusBar().showMessage("Index : {index} ; {delta} = {value}".format(
                index=index, delta= u"\u03B4", value = str(value)))

        

    def init_chart(self):

        self.barset = QBarSet("Residues")
        self.selected = QBarSet("Selected")
        self.selected.setColor(QColor("orange"))

        self.barset.hovered.connect(self.bar_info)
        self.selected.hovered.connect(self.bar_info)

        for index, val in enumerate(np.random.randint(0, 100, 100)):
            self.barset << 0
            self.selected << 0

        self.plot()

        self.series = QStackedBarSeries()
        self.series.setBarWidth(0.5)
        self.series.append(self.barset)
        self.series.append(self.selected)


        # Cut-off line
        self.lineSeries = QLineSeries()
        pen = self.lineSeries.pen()
        pen.setWidth(1)
        pen.setColor(QColor(255, 0, 0))
        pen.setStyle(QtCore.Qt.DashLine)
        pen.setDashPattern([4, 4])
        self.lineSeries.setPen(pen)
        # init at 0
        self.lineSeries.append(QtCore.QPoint(0,0))
        self.lineSeries.append(QtCore.QPoint(100,0))

        # setup X axis
        categories = list(str(val) for val in range(100))
        axis = QBarCategoryAxis()
        axis.append(categories)
        axis.setLabelsAngle(90)
        #axis.setLabelsFont(QFont("free", 8))

        # Create chart
        self.chart = QChart()
        self.chart.addSeries(self.series)
        self.chart.addSeries(self.lineSeries)
        #self.chart.setTitle("kanar")
        self.chart.setAnimationOptions(QChart.SeriesAnimations)
        self.chart.createDefaultAxes()
        self.chart.setAxisX(axis, self.series)
        self.chart.legend().setVisible(False)
        # self.chart.legend().setAlignment(QtCore.Qt.AlignBottom)
        self.chart.setAnimationDuration(0)
        self.chart.layout().setContentsMargins(0,0,0,0)
        self.chart.setMargins(QtCore.QMargins(0,0,0,0))

        # insert in UI
        self.chartview.setChart(self.chart)
        self.chartview.setRenderHint(QPainter.Antialiasing)
