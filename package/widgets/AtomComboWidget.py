

from PyQt5.QtWidgets import QComboBox, QVBoxLayout, QWidget


class AtomComboWidget(QComboBox):
    def __init__(self, comboList, parent=None):
        super().__init__(parent)
        
    def update_options(self, options):
        for combo in self.combos:
            combo.clear()
            for opt in options:
                combo.addItem(opt)
