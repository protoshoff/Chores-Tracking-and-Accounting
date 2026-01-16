import sys
from datetime import datetime
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QLabel, QHBoxLayout, QVBoxLayout, QWidget, QFrame
from PySide6.QtCore import Qt, QTimer

from .views.home import HomeView
from .views.dashboard import KidDashboardView
from .views.approval_queue import ApprovalQueueView
from .views.admin_wifi import AdminWifiView
from .views.quest_log import QuestLogView # Keeping for ref/future

class HeaderWidget(QFrame): 
    # Re-introducing Header but styling it transparently later if needed
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Header")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        
        self.lbl_title = QLabel("CHORE TRACKER")
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
        self.update_clock()

    def update_clock(self):
        now = datetime.now()
        self.lbl_clock.setText(now.strftime("%a %I:%M %p"))

class KioskApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chores Kiosk - SciFi Mode")
        self.setGeometry(0, 0, 1024, 600)
        
        # Load Styles (Sci-Fi)
        try:
            with open("kiosk/styles_sci_fi.qss", "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print("Warning: styles_sci_fi.qss not found")

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
        self.view_home = HomeView()
        self.view_dash = KidDashboardView()
        self.view_approvals = ApprovalQueueView()
        self.view_wifi = AdminWifiView()
        self.view_quest = QuestLogView()
        
        self.stack.addWidget(self.view_home)      # 0
        self.stack.addWidget(self.view_dash)      # 1
        self.stack.addWidget(self.view_approvals) # 2
        self.stack.addWidget(self.view_wifi)      # 3
        self.stack.addWidget(self.view_quest)     # 4
        
        # Signals
        self.view_home.kid_selected.connect(self.go_to_dashboard)
        self.view_home.parent_zone_clicked.connect(self.go_to_approvals)
        self.view_home.admin_clicked.connect(self.go_to_wifi)
        
        self.view_dash.back_clicked.connect(self.go_to_home)
        self.view_approvals.back_clicked.connect(self.go_to_home)
        self.view_wifi.back_clicked.connect(self.go_to_home)
        self.view_quest.close_clicked.connect(self.go_to_home) # Just in case we link it later
        
        self.show()

    def go_to_dashboard(self, kid_id):
        self.view_dash.load_kid(kid_id)
        self.stack.setCurrentIndex(1)
        
    def go_to_approvals(self):
        self.view_approvals.refresh()
        self.stack.setCurrentIndex(2) 

    def go_to_wifi(self):
        self.stack.setCurrentIndex(3)
        
    def go_to_home(self):
        self.view_home.refresh_data() 
        self.stack.setCurrentIndex(0)
