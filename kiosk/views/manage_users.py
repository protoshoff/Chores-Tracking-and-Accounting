from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Signal
from ..components.holo_widgets import HoloButton

class ManageUsersView(QWidget):
    back_clicked = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        btn = HoloButton("BACK")
        btn.clicked.connect(self.back_clicked.emit)
        layout.addWidget(btn)
        layout.addWidget(QLabel("MANAGE USERS - COMING SOON"))
