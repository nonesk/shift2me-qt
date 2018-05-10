from PyQt5.QtCore import QObject, Qt, QPoint
from PyQt5.QtWidgets import QDoubleSpinBox, QHeaderView

from PyQt5.QtChart import (QBarCategoryAxis, QBarSeries, QBarSet, QChart, QAreaSeries,
                           QLineSeries, QStackedBarSeries, QValueAxis, QVXYModelMapper )
from PyQt5.QtGui import QPainter

from package.classes.protocole import TitrationProtocole
from package.models.DataFrameModel import ProtocoleModel
from package.delegates.SpinBoxDelegate import SpinBoxDelegate

class ProtocoleController(QObject):

    def __init__(self, parent):
        super().__init__(parent)

        self.protocole = TitrationProtocole()
        self.protocole.update()
        self.protocoleModel = ProtocoleModel(self.protocole, self)
        parent.ui.protocoleTable.setModel(self.protocoleModel)
        self.delegate = SpinBoxDelegate()
        self.table = parent.ui.protocoleTable
        self.table.setItemDelegateForColumn(0, self.delegate)
        for sectionIndex in range(self.protocoleModel.columnCount()):
            self.table.horizontalHeader().setSectionResizeMode(sectionIndex, QHeaderView.Stretch)
            #self.table.setColumnWidth(colIndex, self.table.width())
        
        
        self.volumeChartView = parent.ui.volumeChartView
        self.volumeChart = QChart()
        self.concChartView = parent.ui.concChartView
        self.concChart = QChart()
        
        parent.ui.titrantName.textEdited.connect(self.protocole.titrant.setName)
        parent.ui.titrantConc.valueChanged.connect(self.set_titrant_concentration)

        parent.ui.analyteName.textEdited.connect(self.protocole.analyte.setName)
        parent.ui.analyteConc.valueChanged.connect(self.set_analyte_concentration)

        parent.ui.analyteInitialVolume.valueChanged.connect(self.set_analyte_volume)
        parent.ui.totalInitialVolume.valueChanged.connect(self.set_initial_volume)

        parent.ui.addStepBtn.clicked.connect(self.add_step)

        self.protocoleModel.modelReset.connect(self.onModelReset)
        self.protocoleModel.rowsInserted.connect(self.onModelReset)



        
        for section, value in enumerate(self.headers):
            self.protocoleModel.setHeaderData(section, Qt.Horizontal, value)

        
        # self.add_step()
        self.table.setColumnHidden(6, True)
        self.init_volume_chart()
        self.init_conc_chart()

    def init_conc_chart(self):
        
        self.titrantSeries = QLineSeries()
        self.titrantSeries.setName("[titrant]")
        
        self.titrantMapper = QVXYModelMapper(self)
        self.titrantMapper.setXColumn(6)
        self.titrantMapper.setYColumn(3)
        self.titrantMapper.setSeries(self.titrantSeries)
        self.titrantMapper.setModel(self.protocoleModel)

        self.analyteSeries = QLineSeries()
        self.analyteSeries.setName("[analyte]")
        
        self.analyteMapper = QVXYModelMapper(self)
        self.analyteMapper.setXColumn(6)
        self.analyteMapper.setYColumn(4)
        self.analyteMapper.setSeries(self.analyteSeries)
        self.analyteMapper.setModel(self.protocoleModel)

        stepAxis = QValueAxis()
        stepAxis.setTickCount(self.protocoleModel.rowCount()+1)
        stepAxis.setTitleText("Step")
        stepAxis.setLabelFormat("%i")
        self.concChart.setAxisX(stepAxis, self.titrantSeries)

        self.concAxis = QValueAxis()
        self.concAxis.setTitleText("Concentration (µM)")
        self.concChart.addAxis(self.concAxis, Qt.AlignLeft)

        self.concChart.addSeries(self.titrantSeries)
        self.concChart.addSeries(self.analyteSeries)

        self.titrantSeries.attachAxis(stepAxis)
        self.titrantSeries.attachAxis(self.concAxis)
        
        self.analyteSeries.attachAxis(stepAxis)
        self.analyteSeries.attachAxis(self.concAxis)

        self.concChartView.setChart(self.concChart)
        self.concChartView.setRenderHint(QPainter.Antialiasing)

    def init_volume_chart(self):
        self.volumeSeries = QLineSeries()
        self.volumeSeries.setName("Titrant volume")
        self.volumeSeries.setPointsVisible()

        self.totalVolumeSeries = QLineSeries()
        self.totalVolumeSeries.setName("Total volume")
        self.totalVolumeSeries.setPointsVisible()

        # self.areaSeries = QAreaSeries(self.volumeSeries, self.totalVolumeSeries)

        self.mapper = QVXYModelMapper(self)
        self.mapper.setXColumn(6)
        self.mapper.setYColumn(1)
        self.mapper.setSeries(self.volumeSeries)
        self.mapper.setModel(self.protocoleModel)

        self.totalVolumeMapper = QVXYModelMapper(self)
        self.totalVolumeMapper.setXColumn(6)
        self.totalVolumeMapper.setYColumn(2)
        self.totalVolumeMapper.setSeries(self.totalVolumeSeries)
        self.totalVolumeMapper.setModel(self.protocoleModel)

        



        self.stepAxis = QValueAxis()
        self.stepAxis.setTickCount(self.protocoleModel.rowCount()+1)
        self.stepAxis.setTitleText("Step")
        self.stepAxis.setLabelFormat("%i")

        
        self.volumeChart.addSeries(self.volumeSeries)
        self.volumeChart.addSeries(self.totalVolumeSeries)
        
        # self.volumeChart.addSeries(self.areaSeries)
        self.volumeChart.setAxisX(self.stepAxis, self.volumeSeries)

        self.volumeAxis = QValueAxis()
        self.volumeAxis.setLinePenColor(self.volumeSeries.pen().color())
        self.volumeAxis.setTitleText("Volume (µL)")
        self.volumeChart.addAxis(self.volumeAxis, Qt.AlignLeft)

        

        self.volumeSeries.attachAxis(self.stepAxis)
        self.volumeSeries.attachAxis(self.volumeAxis)
        self.totalVolumeSeries.attachAxis(self.stepAxis)
        self.totalVolumeSeries.attachAxis(self.volumeAxis)
        
        

        self.volumeChartView.setChart(self.volumeChart)
        self.volumeChartView.setRenderHint(QPainter.Antialiasing)
        

    def volumes(self):
        for row in range(self.protocoleModel.rowCount()):
            yield self.protocoleModel.data(self.protocoleModel.index(row, 0), Qt.DisplayRole)

    def onModelReset(self):
        for row in range(1, self.protocoleModel.rowCount()):
            index = self.protocoleModel.index(row, 0)
            self.table.openPersistentEditor(index)

        self.volumeChart.axisX().setRange(0, self.protocoleModel.rowCount()-1)
        self.volumeChart.axisX().setTickCount(self.protocoleModel.rowCount())

        self.concChart.axisX().setRange(0, self.protocoleModel.rowCount()-1)
        self.concChart.axisX().setTickCount(self.protocoleModel.rowCount())
        
        self.mapper.setRowCount(self.protocoleModel.rowCount())
        self.volumeChart.axisY().setRange(0, self.protocoleModel.data(self.protocoleModel.index(self.protocoleModel.rowCount()-1, 2)).value()+1)
        self.concAxis.setRange(0, max(
            self.protocoleModel.data(self.protocoleModel.index(self.protocoleModel.rowCount()-1, 3)).value(),
            self.protocoleModel.data(self.protocoleModel.index(0,4)).value()
            ))
        print(self.volumeSeries.pointsVector())

    def set_analyte_volume(self, volume):
        self.protocoleModel.modelAboutToBeReset.emit()
        self.protocole.set_analyte_volume(volume)
        self.protocoleModel.modelReset.emit()

    def set_initial_volume(self, volume):
        self.protocoleModel.modelAboutToBeReset.emit()
        self.protocole.set_initial_volume(volume)
        self.protocoleModel.modelReset.emit()

    def set_analyte_concentration(self, concentration):
        self.protocoleModel.modelAboutToBeReset.emit()
        self.protocole.analyte.setConcentration(concentration)
        self.protocole.update()
        self.protocoleModel.modelReset.emit()

    def set_titrant_concentration(self, concentration):
        self.protocoleModel.modelAboutToBeReset.emit()
        self.protocole.titrant.setConcentration(concentration)
        self.protocole.update()
        self.protocoleModel.modelReset.emit()

    def add_step(self):
        self.protocoleModel.insertRows(self.protocoleModel.rowCount(), 1)

    @property
    def headers(self):
        headers = list(map(
            lambda s: s.format(
                titrant=self.protocole.titrant.name,
                analyte=self.protocole.analyte.name),
            [
                'Added {titrant} (µL)',
                'Total {titrant} (µL)',
                'Total volume (µL)',
                '[{titrant}] (µM)',
                '[{analyte}] (µM)',
                '[{titrant}]/[{analyte}]'
            ]))
        return headers

    