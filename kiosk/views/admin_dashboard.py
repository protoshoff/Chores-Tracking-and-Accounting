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
        from ..components.holo_keyboard import HoloKeyboard
        from ..components.holo_alert import HoloAlert
        from ..services.api import ApiService
        
        # 1. Ask for New PIN
        dlg = HoloKeyboard(self.window(), "", title="ENTER NEW PIN")
        self._center_dialog(dlg)
        
        if dlg.exec():
            new_pin = dlg.get_text()
            if len(new_pin) < 4:
                HoloAlert("INVALID", "PIN must be at least 4 digits.", self.window(), is_error=True).exec()
                return

            # 2. Confirm PIN
            dlg_confirm = HoloKeyboard(self.window(), "", title="CONFIRM PIN")
            self._center_dialog(dlg_confirm)
            
            if dlg_confirm.exec():
                confirm_pin = dlg_confirm.get_text()
                
                if new_pin != confirm_pin:
                    HoloAlert("MISMATCH", "PINs did not match. Please try again.", self.window(), is_error=True).exec()
                    return
                    
                # 3. Update API
                success = ApiService.update_pin(new_pin)
                if success:
                    HoloAlert("SUCCESS", "System access code updated successfully.", self.window()).exec()
                else:
                    HoloAlert("ERROR", "Failed to update PIN. Check logs.", self.window(), is_error=True).exec()

    def _center_dialog(self, dlg):
        rect = self.window().geometry()
        dlg.move(
            rect.center().x() - dlg.width() // 2,
            rect.center().y() - dlg.height() // 2
        )
