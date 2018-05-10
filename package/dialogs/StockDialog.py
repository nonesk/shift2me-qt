import qtawesome as qta
from PyQt5 import QtGui, QtWidgets
from package.ui.ui_stock_dialog import Ui_Dialog

class StockDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.patch_ui()

    def patch_ui(self):
        self.ui.addBtn.setIcon(qta.icon('fa.plus'))
        self.ui.updateBtn.setIcon(qta.icon('fa.edit'))
        self.ui.deleteBtn.setIcon(qta.icon('fa.remove'))