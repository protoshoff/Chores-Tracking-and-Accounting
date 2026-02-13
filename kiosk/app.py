import sys
import time
from datetime import datetime
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QLabel, QHBoxLayout, QVBoxLayout, QWidget, QFrame
from PySide6.QtCore import Qt, QTimer, QEvent

from .views.home import HomeView
from .views.dashboard import KidDashboardView
from .views.approval_queue import ApprovalQueueView
from .views.admin_wifi import AdminWifiView
from .views.reports import ReportsView
from .views.screensaver import ScreensaverView
from .views.quest_log import QuestLogView # Keeping for ref/future
from .views.pin_pad import PinPad
from .views.admin_dashboard import AdminDashboardView
from .views.manage_users import ManageUsersView
from .views.manage_chores import ManageChoresView

class HeaderWidget(QFrame): 
    # Re-introducing Header but styling it transparently later if needed
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Header")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        
        self.lbl_title = QLabel("QUEST TRACKER")
        self.lbl_title.setObjectName("HoloHeader") # Use new ID
        layout.addWidget(self.lbl_title)
        
        layout.addStretch()
        
        self.lbl_clock = QLabel("Time")
        self.lbl_clock.setObjectName("HoloHeader")
        layout.addWidget(self.lbl_clock)
        
        # Clock Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(1000)
        
        # Load configured timezone from API
        self.load_timezone()
        
        # Update clock immediately
        self.update_clock()

    def load_timezone(self):
        """Load configured timezone from API"""
        try:
            from .services.api import ApiService
            config = ApiService.get_system_config()
            if config:
                self.configured_timezone = config.get("timezone")
        except:
            pass

    def update_clock(self):
        """Update clock display using configured or system timezone."""
        import os
        
        # Apply configured timezone if set
        if self.configured_timezone:
            try:
                os.environ['TZ'] = self.configured_timezone
                time.tzset()
            except:
                pass
        
        # Use time.localtime() which automatically respects system timezone
        # Works on all Python versions (no zoneinfo dependency)
        local_time = time.localtime()
        now = datetime.fromtimestamp(time.mktime(local_time))
        self.lbl_clock.setText(now.strftime("%a %I:%M %p"))

class KioskApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chores Kiosk - SciFi Mode")
        self.setGeometry(0, 0, 1024, 600)
        
        # Load Styles (Sci-Fi)
        # Load Fonts
        from PySide6.QtGui import QFontDatabase
        import os
        font_dir = os.path.join(os.path.dirname(__file__), "assets", "fonts")
        if os.path.exists(font_dir):
            for f in os.listdir(font_dir):
                if f.endswith(".ttf"):
                    font_id = QFontDatabase.addApplicationFont(os.path.join(font_dir, f))
                    if font_id != -1:
                        families = QFontDatabase.applicationFontFamilies(font_id)
                        print(f"DEBUG: Loaded Font File {f} -> Families: {families}")
                    else:
                        print(f"DEBUG: Failed to load font {f}")
        
        # Debug: Print available font families to check for Roboto/Orbitron
        print("DEBUG: Available Font Families (Partial):", QFontDatabase.families()[:50])
        if "Orbitron" in QFontDatabase.families(): print("DEBUG: Orbitron CONFIRMED")
        else: print("DEBUG: Orbitron MISSING")
        if "Roboto" in QFontDatabase.families(): print("DEBUG: Roboto CONFIRMED")
        else: print("DEBUG: Roboto MISSING")
        
        # Load Stylesheet
        try:
            import os
            # Theme Configuration
            THEME_NAME = "modern_admin_v2.qss" 
            # Options: "scifi_v1.qss", "modern_admin.qss", "modern_admin_v2.qss"
            
            base_dir = os.path.dirname(os.path.dirname(__file__)) # Go up from kiosk/app.py to root
            theme_path = os.path.join(base_dir, "kiosk", "themes", THEME_NAME)
            
            with open(theme_path, "r") as f:
                style_content = f.read()
                print(f"DEBUG: Loading Theme: {THEME_NAME}")
                self.setStyleSheet(style_content)
        except Exception as e:
            print(f"Warning: Theme {THEME_NAME} not found. Error: {e}")

        # Central Container
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(0)
        
        # Header
        self.header = HeaderWidget()
        main_layout.addWidget(self.header)
        
        # Stacked Views
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)
        
        # Init Views
        print("DEBUG: Init HomeView...")
        self.view_home = HomeView()
        print("DEBUG: Init KidDashboardView...")
        self.view_dash = KidDashboardView()
        print("DEBUG: Init ApprovalQueueView...")
        self.view_approvals = ApprovalQueueView()
        print("DEBUG: Init AdminDashboardView...")
        self.view_admin = AdminDashboardView()
        
        print("DEBUG: Init AdminWifiView...")
        self.view_wifi = AdminWifiView()
        print("DEBUG: Init ManageUsersView...")
        self.view_users = ManageUsersView()
        print("DEBUG: Init ManageChoresView...")
        self.view_chores = ManageChoresView()
        print("DEBUG: Init QuestLogView...")
        self.view_quest = QuestLogView()
        
        print("DEBUG: Init ReportsView...")
        self.view_reports = ReportsView()
        
        print("DEBUG: Init LedgerView...")
        try:
            from .views.ledger import LedgerView
            self.view_ledger = LedgerView()
        except Exception as e:
            print(f"CRITICAL ERROR initializing LedgerView: {e}")
            import traceback
            traceback.print_exc()
            # Create a dummy widget so stack doesn't crash on addWidget
            self.view_ledger = QWidget()
        print("DEBUG: Init ScreensaverView...")
        self.view_saver = ScreensaverView()
        
        print("DEBUG: Init SettingsView...")
        from .views.settings import SettingsView
        self.view_settings = SettingsView()
        
        print("DEBUG: Adding widgets to stack...")
        self.stack.addWidget(self.view_home)      # 0
        self.stack.addWidget(self.view_dash)      # 1
        self.stack.addWidget(self.view_approvals) # 2
        self.stack.addWidget(self.view_admin)     # 3 (Admin Landing)
        self.stack.addWidget(self.view_wifi)      # 4
        self.stack.addWidget(self.view_users)     # 5
        self.stack.addWidget(self.view_chores)    # 6
        self.stack.addWidget(self.view_quest)     # 7
        self.stack.addWidget(self.view_reports)   # 8 
        self.stack.addWidget(self.view_saver)     # 9
        self.stack.addWidget(self.view_ledger)    # 10
        self.stack.addWidget(self.view_settings)  # 11 (NEW)
        
        # Signals
        print("DEBUG: Widgets added.")
        
        # Signals
        print("DEBUG: Connecting signals...")
        self.view_home.kid_selected.connect(self.go_to_dashboard)
        self.view_home.parent_zone_clicked.connect(self.go_to_approvals)
        self.view_home.admin_clicked.connect(self.go_to_admin_auth)
        
        self.view_dash.back_clicked.connect(self.go_to_home)
        self.view_approvals.back_clicked.connect(self.go_to_home)
        
        # Admin Nav
        self.view_admin.back_clicked.connect(self.go_to_home)
        self.view_admin.wifi_clicked.connect(lambda: self.stack.setCurrentIndex(4))
        self.view_admin.users_clicked.connect(lambda: self.stack.setCurrentIndex(5))
        self.view_admin.chores_clicked.connect(lambda: self.stack.setCurrentIndex(6))
        self.view_admin.reports_clicked.connect(lambda: self.stack.setCurrentIndex(8)) 
        self.view_admin.ledger_clicked.connect(self.prompt_ledger_kid)
        self.view_admin.settings_clicked.connect(lambda: self.stack.setCurrentIndex(11))
        
        self.view_wifi.back_clicked.connect(self.go_to_admin_menu)
        self.view_users.back_clicked.connect(self.go_to_admin_menu)
        self.view_chores.back_clicked.connect(self.go_to_admin_menu)
        self.view_reports.back_clicked.connect(self.go_to_admin_menu)
        self.view_ledger.back_clicked.connect(self.go_to_admin_menu)
        self.view_settings.back_clicked.connect(self.go_to_admin_menu)
        
        self.view_quest.close_clicked.connect(self.go_to_home)
        self.view_saver.wake_up.connect(self.wake_up)
        
        print("DEBUG: Starting idle timer...")
        # Idle Timer
        self.idle_timer = QTimer(self)
        self.idle_timer.timeout.connect(self.enter_screensaver)
        self.idle_timer.start(120000) # 2 minutes
        
        print("DEBUG: Installing event filter...")
        # Install Event Filter to catch all input
        QApplication.instance().installEventFilter(self)
        
        print("DEBUG: KioskApp Init COMPLETE.")
        # self.show() -> Moved to main.py to handle args better

    def eventFilter(self, obj, event):
        if event.type() in (QEvent.MouseButtonPress, QEvent.MouseMove, QEvent.KeyPress, QEvent.TouchBegin):
             self.idle_timer.start(120000) # Reset timer on any input
        return super().eventFilter(obj, event)

    def enter_screensaver(self):
        if self.stack.currentIndex() != 9:
            self.stack.setCurrentIndex(9)
            
    def wake_up(self):
        # Always return to HOME for security (auto-lock)
        self.go_to_home()

    def go_to_dashboard(self, kid_id):
        self.view_dash.load_kid(kid_id)
        self.stack.setCurrentIndex(1)
        
    def go_to_approvals(self):
        # Security Check
        dlg = PinPad(self)
        if dlg.exec():
            self.view_approvals.refresh()
            self.stack.setCurrentIndex(2) 
            
    def go_to_admin_auth(self):
        # Security Check
        dlg = PinPad(self)
        if dlg.exec():
             self.stack.setCurrentIndex(3)
             
    def go_to_admin_menu(self):
        self.stack.setCurrentIndex(3)
        
    def go_to_home(self):
        self.view_home.refresh_data() 
        self.stack.setCurrentIndex(0)

    def prompt_ledger_kid(self):
        # Quick Dialog to pick kid
        # We need imports here to avoid circular at top if any, but local import is safer
        from PySide6.QtWidgets import QDialog, QVBoxLayout
        from .components.holo_widgets import HoloButton
        from .services.api import ApiService
        
        kids = ApiService.get_kids()
        if not kids: return
        
        dlg = QDialog(self)
        dlg.setWindowTitle("SELECT CREW MEMBER")
        dlg.setFixedSize(400, 100 + (len(kids)*70))
        dlg.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        dlg.setStyleSheet("background-color: #050510; border: 2px solid #00F0FF;")
        
        layout = QVBoxLayout(dlg)
        
        selected_id = None
        
        def pick(kid_id):
            nonlocal selected_id
            selected_id = kid_id
            dlg.accept()
            
        for k in kids:
            btn = HoloButton(k["name"])
            btn.clicked.connect(lambda checked=False, kid=k: pick(kid["id"]))
            layout.addWidget(btn)
            
        btn_cancel = HoloButton("CANCEL", is_primary=False)
        btn_cancel.clicked.connect(dlg.reject)
        layout.addWidget(btn_cancel)
        
        if dlg.exec() and selected_id is not None:
             self.view_ledger.load_kid(selected_id)
             self.stack.setCurrentIndex(10)
