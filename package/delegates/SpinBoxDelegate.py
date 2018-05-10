from PyQt5.QtWidgets import QStyledItemDelegate, QDoubleSpinBox
from PyQt5.QtCore import Qt

class SpinBoxDelegate(QStyledItemDelegate):

    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        editor = QDoubleSpinBox(parent)
        editor.setMinimum(1)
        editor.setFrame(False)
        editor.setAlignment(Qt.AlignHCenter)
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole).value()
        editor.setValue(value)

    def setModelData(self, editor, model, index):
        editor.interpretText()
        value = editor.value()
        model.setData(index,value, Qt.EditRole)
    
