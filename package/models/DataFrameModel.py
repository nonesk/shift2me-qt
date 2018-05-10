import pandas as pd
from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt, QVariant
from PyQt5.QtGui import QFont, QBrush, QColor
from PyQt5.QtWidgets import QPushButton
from package.classes.protocole import TitrationProtocole

class DataFrameModel(QAbstractTableModel):

    def __init__(self, parent=None, editable = False):
        super().__init__(parent)

        self._df = pd.DataFrame()
        self.editable = editable
        
        
    @property
    def df(self):
        return self._df

    def load_csv(self, filePath, header):
        with open(filePath, "r") as fh:
            self._df = pd.read_table(fh, sep='\\s+', header=header)
            self.modelReset.emit()

    def rowCount(self, parent=QModelIndex()):
        return len(self.df.index)

    def columnCount(self, parent=QModelIndex()):
        return len(self.df.columns.values)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return QVariant()

        if orientation == Qt.Horizontal:
            try:
                return str(self.df.columns.tolist()[section])
            except (IndexError, ):
                return QVariant()
        elif orientation == Qt.Vertical:
            try:
                # return self.df.index.tolist()
                return str(self.df.index.tolist()[section])
            except (IndexError, ):
                return QVariant()

    

    def data(self, index, role=Qt.DisplayRole):

        row = self.df.index[index.row()]
        col = self.df.columns[index.column()]

        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            return QVariant(str(self.df.ix[row, col]))
        return None

    def sort(self, column, order):
        colname = self.df.columns.tolist()[column]
        self.layoutAboutToBeChanged.emit()
        self.df.sort_values(colname, ascending= order == Qt.AscendingOrder, inplace=True)
        self.df.reset_index(inplace=True, drop=True)
        self.layoutChanged.emit()

    def flags(self,index):
        #return super().flags(index)
        flags = super().flags(index)
        if self.editable : flags |= Qt.ItemIsEditable
        return flags

    def setData(self, index, value, role=Qt.DisplayRole):
        """Set the value to the index position depending on Qt::ItemDataRole and data type of the column
        Args:
            index (QModelIndex): Index to define column and row.
            value (object): new value.
            role (Qt::ItemDataRole): Use this role to specify what you want to do.
        Raises:
            TypeError: If the value could not be converted to a known datatype.
        Returns:
            True if value is changed. Calls layoutChanged after update.
            False if value is not different from original value.
        """
        if not index.isValid():
            return False

        if value != index.data(role):

            self.layoutAboutToBeChanged.emit()

            row = self.df.index[index.row()]
            col = self.df.columns[index.column()]
            #print 'before change: ', index.data().toUTC(), self.df.iloc[row][col]
            self.df.set_value(row, col, value)
            #print 'after change: ', value, self._dataFrame.iloc[row][col]
            self.layoutChanged.emit()
            return True
        else:
            return False


class ProtocoleModel(DataFrameModel):

    def __init__(self, protocole, parent = None, editable = True):
        super().__init__(parent, editable)
        self.protocole = protocole
        self.headers = self.df.columns.tolist()

    @property
    def df(self):
        return self.protocole.df

    def flags(self,index):
        #return super().flags(index)
        flags = Qt.ItemIsSelectable
        # if index.row() != 0:
        flags |= Qt.ItemIsEnabled
        if self.editable and index.column() == 0 and index.row() != 0:
            flags |= Qt.ItemIsEditable
        return flags


    def data(self, index, role=Qt.DisplayRole):

        if not index.isValid():
            return None


        row = self.df.index[index.row()]
        col = self.df.columns[index.column()]

        
        if role == Qt.DisplayRole:
            return QVariant(float(self.df.ix[row, col]))
        elif role == Qt.EditRole:
            return QVariant(float(self.df.ix[row,col]))
        elif role == Qt.FontRole:
            if index.column() == 0 and index.row() != 0:
                font = QFont()
                font.setBold(True)
                return QVariant(font)
        elif role == Qt.TextAlignmentRole:
            if index.column() == 0 and index.row() != 0:
                return Qt.AlignCenter
        elif role == Qt.BackgroundRole:
            if index.column() == 0 and index.row() != 0:
                return QBrush(QColor(100, 200, 255, 100))
        elif role == Qt.ForegroundRole:
            if index.column() == 0 and index.row() != 0:
                return QBrush(QColor(100, 200, 50))
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):

        if role == Qt.StatusTipRole:
            return QVariant("KANAR")
        if role != Qt.DisplayRole:
            return QVariant()

        if orientation == Qt.Horizontal:
            try:
                return str(self.headers[section])
            except (IndexError, ):
                return QVariant()
        elif orientation == Qt.Vertical:
            try:
                # return self.df.index.tolist()
                return "Step {}".format(self.df.index.tolist()[section])
            except (IndexError, ):
                return QVariant()

    def setHeaderData(self, section, orientation, value, role= Qt.EditRole):
        if orientation == Qt.Horizontal:
            self.headers[section] = value
            self.headerDataChanged.emit(Qt.Horizontal, section, section )
            return True
        return False

    def setData(self, index, value, role=Qt.DisplayRole):
        """Set the value to the index position depending on Qt::ItemDataRole and data type of the column
        Args:
            index (QModelIndex): Index to define column and row.
            value (object): new value.
            role (Qt::ItemDataRole): Use this role to specify what you want to do.
        Raises:
            TypeError: If the value could not be converted to a known datatype.
        Returns:
            True if value is changed. Calls layoutChanged after update.
            False if value is not different from original value.
        """
        if not index.isValid():
            return False

        if value != index.data(role):

            self.modelAboutToBeReset.emit()

            row = self.df.index[index.row()]
            col = self.df.columns[index.column()]
            #print 'before change: ', index.data().toUTC(), self.df.iloc[row][col]
            self.protocole.update_volumes({row: value})
            self.protocole.update()
            #print 'after change: ', value, self._dataFrame.iloc[row][col]
            self.modelReset.emit()
            return True
        
        return False

    
    def insertRows(self, row, count, parent=QModelIndex()):
        self.beginInsertRows(parent, self.rowCount(), self.rowCount())
        self.protocole.add_volume(self.protocole.volumes[-1] or 1)
        self.endInsertRows()
        return True