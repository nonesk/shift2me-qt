from PyQt5.QtWidgets import QFileSystemModel
from PyQt5.QtCore import Qt

class FileSystemModel(QFileSystemModel):

    def __init__(self, *args, **kwargs):
        super().__init__()

    def supportedDropActions(self):
        return Qt.DropActions(Qt.MoveAction | Qt.TargetMoveAction)