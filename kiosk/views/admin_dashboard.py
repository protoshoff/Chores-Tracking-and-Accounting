from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout
from PySide6.QtCore import Signal, Qt
from ..components.holo_widgets import HoloButton, HoloFrame

class AdminDashboardView(QWidget):
    back_clicked = Signal()
    users_clicked = Signal()
    chores_clicked = Signal()
    wifi_clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        main = QVBoxLayout(self)
        
        # --- Header ---
        top = QHBoxLayout()
        btn_back = HoloButton("← BACK", is_primary=False)
        btn_back.setFixedSize(120, 50)
        btn_back.clicked.connect(self.back_clicked.emit)
        top.addWidget(btn_back)
        
        lbl_title = QLabel("SYSTEM CONFIGURATION")
        lbl_title.setObjectName("HoloHeader")
        top.addWidget(lbl_title)
        top.addStretch()
        main.addLayout(top)
        
        # --- Menu Grid ---
        grid_wrapper = QWidget()
        grid = QGridLayout(grid_wrapper)
        grid.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid.setSpacing(40)
        main.addWidget(grid_wrapper, 1)
        
        # 1. Users
        btn_users = HoloButton("MANAGE CREW")
        btn_users.setFixedSize(300, 150)
        btn_users.clicked.connect(self.users_clicked.emit)
        grid.addWidget(btn_users, 0, 0)
        
        # 2. Chores
        btn_chores = HoloButton("MANAGE QUESTS")
        btn_chores.setFixedSize(300, 150)
        btn_chores.clicked.connect(self.chores_clicked.emit)
        grid.addWidget(btn_chores, 0, 1)
        
        # 3. WiFi
        btn_wifi = HoloButton("COMM LINK (WiFi)")
        btn_wifi.setFixedSize(300, 150)
        btn_wifi.clicked.connect(self.wifi_clicked.emit)
        grid.addWidget(btn_wifi, 1, 0)
        
        # 4. Settings (Placeholder or System Info)
        btn_sys = HoloButton("SYSTEM INFO", is_primary=False)
        btn_sys.setFixedSize(300, 150)
        # btn_sys.clicked.connect(...)
        grid.addWidget(btn_sys, 1, 1)
