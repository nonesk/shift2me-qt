import os

from PyQt5.QtWidgets import (QDialog, QDialogButtonBox, QFormLayout, 
    QPushButton, QDialogButtonBox, QFileDialog, QHBoxLayout, QLabel, 
    QGroupBox, QVBoxLayout, QFrame, QListView,)
from PyQt5.QtGui import QIcon

class NewExperiment(QDialog):
    """A modal window to parameter a new experiment
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('New Experiment')
        self.resize(800, 600)
        
        
        self.directory = os.path.os.getcwd() # project directory
        self.dirLabel = QLabel(self.directory) # currently set project directory
        
        browseBtn = QPushButton(QIcon.fromTheme('folder'), '', self)

        dataForm = QGroupBox(self.tr('Path to data directory'), self)

        formLayout = QFormLayout(dataForm)
        formLayout.addRow(browseBtn, self.dirLabel)

        modalLayout = QHBoxLayout()
        setupLayout = QVBoxLayout()
        previewLayout = QVBoxLayout()

        setupLayout.addWidget(dataForm)
        setupLayout.addStretch(1)

        fileFrame = QFrame(self)

        previewLayout.addChildWidget(fileFrame)
        previewLayout.addStretch(1)

        

        modalLayout.addLayout(setupLayout)
        modalLayout.addLayout(previewLayout)
        modalLayout.addStretch(1)

        self.setLayout(modalLayout)


        browseBtn.clicked.connect(self.select_directory)
        
    def select_directory(self):
        self.directory = QFileDialog.getExistingDirectory(self, "RMN Data directory", self.directory)
        self.dirLabel.setText(self.directory)
        
