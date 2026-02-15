from PySide6.QtWidgets import QWidget, QGridLayout, QLabel, QVBoxLayout, QHBoxLayout, QProgressBar, QScrollArea
from PySide6.QtCore import Qt, Signal, QTimer
from ..components.holo_widgets import HoloFrame, HoloButton
from ..services.sound import SoundService

class HoloKidCard(HoloFrame):
    clicked = Signal(int) 

    def __init__(self, data, width=300, height=380, parent=None):
        super().__init__(title="", parent=parent) # No title on card frame itself
        self.setObjectName("KidCard")
        self.kid_id = data["id"]
        self.setFixedSize(width, height) # Dynamic size
        
        # Internal layout respecting HoloFrame margins
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Name
        self.name_lbl = QLabel(data["name"])
        self.name_lbl.setObjectName("CardTitle") # White text to match Web Admin
        self.name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.name_lbl)
        
        # Balance
        bal = data.get("balance", 0.0)
        self.bal_lbl = QLabel(f"${bal:.2f}")
        self.bal_lbl.setObjectName("HoloHeader") # Use cyan header style
        self.bal_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.bal_lbl)
        
        layout.addSpacing(10)
        
        # Stats Grid
        stats_layout = QGridLayout()
        
        # Today
        lbl_today_title = QLabel("TODAY:")
        lbl_today_title.setObjectName("QuestDesc") 
        stats_layout.addWidget(lbl_today_title, 0, 0)
        
        summary = data.get("chores_summary", {}) 
        done = summary.get("today_done", 0)
        total = summary.get("today_total", 0)
        
        lbl_today = QLabel(f"{done} / {total}")
        # Inherits generic QWidget white text
        lbl_today.setStyleSheet("font-size: 20px; font-weight: bold;")
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
        self.prog.setTextVisible(True)
        self.prog.setFormat("%p%")  # Show percentage
        wl.addWidget(self.prog)
        
        stats_layout.addWidget(wrapper, 1, 0, 1, 2)
        
        layout.addLayout(stats_layout)
        layout.addStretch()
        
        # Pending Warning
        pending = summary.get("pending_count", 0)
        if pending > 0:
            lbl_pend = QLabel(f"⚠ {pending} PENDING")
            lbl_pend.setStyleSheet("color: #FFD700; font-weight: bold;") # Keep Gold for warnings
            lbl_pend.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(lbl_pend)

    def mousePressEvent(self, event):
        SoundService.play_click()
        self.clicked.emit(self.kid_id)

class HomeView(QWidget):
    kid_selected = Signal(int)
    parent_zone_clicked = Signal()
    admin_clicked = Signal() 

    def __init__(self, parent=None):
        super().__init__(parent)
        
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(5)  # Small spacing between grid and footer
        
        # --- Grid Area ---
        # Use scroll area to handle many crew members without pushing footer off-screen
        grid_wrapper = QWidget()
        self.grid = QGridLayout(grid_wrapper)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        grid_scroll = QScrollArea()
        grid_scroll.setWidget(grid_wrapper)
        grid_scroll.setWidgetResizable(True)
        grid_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        grid_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        main_layout.addWidget(grid_scroll, 1)  # Stretch factor 1 - takes remaining space
        
        # --- Footer ---
        # Ensure footer always stays at bottom and visible
        foot_wrapper = QWidget()
        foot_wrapper.setFixedHeight(100)  # Reserve fixed space for footer
        foot_layout = QHBoxLayout(foot_wrapper)
        foot_layout.setContentsMargins(40, 10, 40, 10)
        
        btn_parent = HoloButton("PARENT ZONE", is_primary=False)
        btn_parent.setFixedSize(220, 60)
        btn_parent.clicked.connect(self.parent_zone_clicked.emit)
        
        btn_admin = HoloButton("SYSTEM", is_primary=False)
        btn_admin.setFixedSize(180, 60)
        btn_admin.clicked.connect(self.admin_clicked.emit)
        
        foot_layout.addWidget(btn_parent)
        foot_layout.addStretch()
        foot_layout.addWidget(btn_admin)
        main_layout.addWidget(foot_wrapper, 0)  # Stretch factor 0 - fixed height
        
        # Auto-Retry Timer
        self.retry_timer = QTimer(self)
        self.retry_timer.timeout.connect(self.refresh_data)
        
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
             # If API fails, show connecting and retry
             kids_data = [{"id": 0, "name": "CONNECTING...", "balance": 0.0}]
             if not self.retry_timer.isActive():
                 self.retry_timer.start(2000) # Retry every 2s
        else:
             # Success - stop retrying
             self.retry_timer.stop()

        count = len(kids_data)
        
        # Responsive Layout Logic
        if count <= 2:
            # 1 or 2 kids: Big Cards, Wide Spacing
            card_w, card_h = 400, 320  # Reduced to fit with spacing + footer on 600px screen
            self.grid.setHorizontalSpacing(150)
            self.grid.setVerticalSpacing(40)  # Also reduced spacing
            MAX_COLS = 2
        elif count == 3:
            # 3 kids: Medium cards, Medium spacing
            card_w, card_h = 350, 300  # Reduced to fit 600px screen
            self.grid.setHorizontalSpacing(80)
            self.grid.setVerticalSpacing(20)  # Reduced spacing
            MAX_COLS = 3
        else:
            # 4+ kids: Standard cards, Tight grid
            card_w, card_h = 280, 280  # Reduced to fit 600px screen
            self.grid.setHorizontalSpacing(20)
            self.grid.setVerticalSpacing(20)
            MAX_COLS = 3

        row, col = 0, 0
        for k in kids_data:
            card = HoloKidCard(k, width=card_w, height=card_h)
            card.clicked.connect(self.on_card_clicked)
            self.grid.addWidget(card, row, col)
            col += 1
            if col >= MAX_COLS:
                col = 0
                row += 1

    def on_card_clicked(self, kid_id):
        self.kid_selected.emit(kid_id)
