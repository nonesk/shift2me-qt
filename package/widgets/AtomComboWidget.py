

from PyQt5.QtWidgets import QComboBox, QWidget, QVBoxLayout

class AtomComboWidget(QWidget):
    def __init__(self, comboList, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.combos = comboList
        for combo in self.combos:
            layout.addWidget(combo)
        self.show()

    def update_options(self, options):
        for combo in self.combos:
            combo.clear()
            for opt in options:
                combo.addItem(opt)
            