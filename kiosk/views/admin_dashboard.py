from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout
from PySide6.QtCore import Signal, Qt
from ..components.holo_widgets import HoloButton, HoloFrame

class AdminDashboardView(QWidget):
    back_clicked = Signal()
    users_clicked = Signal()
    chores_clicked = Signal()
    wifi_clicked = Signal()
    reports_clicked = Signal()
    
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
        
        # 4. Reports
        btn_rep = HoloButton("REPORTS")
        btn_rep.setFixedSize(300, 150)
        btn_rep.clicked.connect(self.reports_clicked.emit)
        grid.addWidget(btn_rep, 1, 1)
        
        # 5. Change PIN
        btn_pin = HoloButton("CHANGE PIN", is_primary=False)
        btn_pin.setFixedSize(300, 100) # Smaller
        btn_pin.clicked.connect(self.change_pin_flow)
        grid.addWidget(btn_pin, 2, 0, 1, 2) # Span 2 columns

    def change_pin_flow(self):
        from .pin_pad import PinPad
        from ..components.holo_keyboard import HoloKeyboard
        from ..services.api import ApiService
        
        # 1. Ask for New PIN using Keyboard (so we get full keypad if needed, or re-use PinPad logic?)
        # Let's use a specialized PinPad mode or just a text dialog.
        # Ideally we want the PinPad UI but for "Entry".
        # For simplicity in v0.1, let's use the HoloKeyboard since it has numbers now.
        
        dlg = HoloKeyboard(self.window(), "")
        # Center
        rect = self.window().geometry()
        dlg.move(
            rect.center().x() - dlg.width() // 2,
            rect.center().y() - dlg.height() // 2
        )
        
        if dlg.exec():
            new_pin = dlg.get_text()
            if len(new_pin) >= 4:
                success = ApiService.update_pin(new_pin)
                # We could show a toast here?
                print(f"PIN Update Success: {success}")
            else:
                print("PIN too short")
