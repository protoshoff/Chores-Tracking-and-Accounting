from PySide6.QtWidgets import QWidget, QGridLayout, QLabel, QVBoxLayout, QHBoxLayout, QProgressBar
from PySide6.QtCore import Qt, Signal
from ..components.holo_widgets import HoloFrame, HoloButton

class HoloKidCard(HoloFrame):
    clicked = Signal(int) 

    def __init__(self, data, parent=None):
        super().__init__(title="", parent=parent) # No title on card frame itself
        self.kid_id = data["id"]
        self.setFixedSize(300, 380) # Adjusted size for glow margins
        
        # Internal layout respecting HoloFrame margins
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Name
        self.name_lbl = QLabel(data["name"])
        self.name_lbl.setObjectName("HoloHeader") # Big Cyan Text
        self.name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.name_lbl)
        
        # Balance
        bal_cents = data.get("balance_cents", 0)
        self.bal_lbl = QLabel(f"${bal_cents/100:.2f}")
        self.bal_lbl.setStyleSheet("font-size: 36px; color: #00E5FF; font-weight: bold;") 
        self.bal_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.bal_lbl)
        
        layout.addSpacing(10)
        
        # Stats Grid
        stats_layout = QGridLayout()
        
        # Today
        lbl_today_title = QLabel("TODAY:")
        lbl_today_title.setObjectName("QuestDesc") # Muted style
        stats_layout.addWidget(lbl_today_title, 0, 0)
        
        summary = data.get("chores_summary", {}) 
        done = summary.get("today_done", 0)
        total = summary.get("today_total", 0)
        
        lbl_today = QLabel(f"{done} / {total}")
        lbl_today.setStyleSheet("font-size: 20px; font-weight: bold; color: white;")
        stats_layout.addWidget(lbl_today, 0, 1)
        
        # Week Progress
        wrapper = QWidget()
        wl = QVBoxLayout(wrapper)
        wl.setContentsMargins(0,0,0,0)
        wl.setSpacing(5)
        
        lbl_week = QLabel("WEEKLY GOAL:")
        lbl_week.setObjectName("QuestDesc")
        wl.addWidget(lbl_week)
        
        self.prog = QProgressBar()
        week_pct = summary.get("week_pct", 0)
        self.prog.setValue(week_pct)
        self.prog.setTextVisible(False)
        wl.addWidget(self.prog)
        
        stats_layout.addWidget(wrapper, 1, 0, 1, 2)
        
        layout.addLayout(stats_layout)
        layout.addStretch()
        
        # Pending Warning
        pending = summary.get("pending_count", 0)
        if pending > 0:
            lbl_pend = QLabel(f"⚠ {pending} PENDING")
            lbl_pend.setStyleSheet("color: #FFD700; font-weight: bold;")
            lbl_pend.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(lbl_pend)

    def mousePressEvent(self, event):
        self.clicked.emit(self.kid_id)

class HomeView(QWidget):
    kid_selected = Signal(int)
    parent_zone_clicked = Signal()
    admin_clicked = Signal() 

    def __init__(self, parent=None):
        super().__init__(parent)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        
        # --- Grid Area ---
        grid_wrapper = QWidget()
        self.grid = QGridLayout(grid_wrapper)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(grid_wrapper, 1) 
        
        # --- Footer ---
        # (No QFrame container needed, just layout)
        foot_layout = QHBoxLayout()
        foot_layout.setContentsMargins(40, 20, 40, 20)
        
        btn_parent = HoloButton("PARENT ZONE", is_primary=False)
        btn_parent.setFixedSize(220, 60)
        btn_parent.clicked.connect(self.parent_zone_clicked.emit)
        
        btn_admin = HoloButton("SYSTEM", is_primary=False)
        btn_admin.setFixedSize(180, 60)
        btn_admin.clicked.connect(self.admin_clicked.emit)
        
        foot_layout.addWidget(btn_parent)
        foot_layout.addStretch()
        foot_layout.addWidget(btn_admin)
        main_layout.addLayout(foot_layout)
        
        # Load Data
        self.refresh_data()

    def refresh_data(self):
        # Clear Grid
        for i in reversed(range(self.grid.count())): 
            item = self.grid.itemAt(i)
            if item.widget(): item.widget().setParent(None)

        from ..services.api import ApiService
        kids_data = ApiService.get_kids()
        
        if not kids_data:
             # Placeholder for dev if API fails
             kids_data = [{"id": 0, "name": "OFFLINE", "balance_cents": 0}]

        row, col = 0, 0
        MAX_COLS = 3
        for k in kids_data:
            card = HoloKidCard(k)
            card.clicked.connect(self.on_card_clicked)
            self.grid.addWidget(card, row, col)
            col += 1
            if col >= MAX_COLS:
                col = 0
                row += 1

    def on_card_clicked(self, kid_id):
        self.kid_selected.emit(kid_id)
