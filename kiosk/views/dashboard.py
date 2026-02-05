from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame, QProgressBar
from PySide6.QtCore import Qt, Signal
from ..services.api import ApiService
from ..components.holo_widgets import HoloFrame, HoloButton

class KidDashboardView(QWidget):
    back_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.kid_id = None
        
        main_layout = QVBoxLayout(self)
        
        # Header Row
        top = QHBoxLayout()
        self.btn_back = HoloButton("← BACK", is_primary=False)
        self.btn_back.setFixedSize(120, 50)
        self.btn_back.clicked.connect(self.back_clicked.emit)
        top.addWidget(self.btn_back)
        
        self.lbl_title = QLabel("DASHBOARD")
        self.lbl_title.setObjectName("HoloHeader")
        top.addWidget(self.lbl_title)
        top.addStretch()
        main_layout.addLayout(top)
        
        # Content Split
        content = QHBoxLayout()
        
        # --- LEFT: Status Panel ---
        self.status_panel = HoloFrame("STATUS")
        self.status_panel.setFixedWidth(350)
        sl = QVBoxLayout(self.status_panel)
        sl.setContentsMargins(30, 80, 30, 40)
        sl.setSpacing(20)
        sl.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.name_lbl = QLabel("-")
        self.name_lbl.setStyleSheet("font-size: 28px; font-weight: bold; color: white;")
        sl.addWidget(self.name_lbl)
        
        self.bal_lbl = QLabel("$0.00")
        self.bal_lbl.setStyleSheet("font-size: 48px; color: #00E5FF; font-weight: bold;")
        sl.addWidget(self.bal_lbl)
        
        # Progress Bars with Labels
        sl.addWidget(QLabel("OFFICIAL PROGRESS:"))
        self.prog_official = QProgressBar()
        self.prog_official.setTextVisible(False)
        sl.addWidget(self.prog_official)
        
        sl.addWidget(QLabel("YOUR PROGRESS:"))
        self.prog_kid = QProgressBar()
        self.prog_kid.setTextVisible(False)
        sl.addWidget(self.prog_kid)
        
        sl.addStretch()
        content.addWidget(self.status_panel)
        
        # --- RIGHT: Quest Logs (Chores) ---
        self.quest_panel = HoloFrame("QUEST LIST")
        ql = QVBoxLayout(self.quest_panel)
        ql.setContentsMargins(30, 80, 30, 40)
        
        # Scroll Area custom style to be transparent inside HoloFrame
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setSpacing(15)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self.scroll_widget)
        
        ql.addWidget(scroll)
        content.addWidget(self.quest_panel)
        
        main_layout.addLayout(content)

    def load_kid(self, kid_id):
        self.kid_id = kid_id
        kid = ApiService.get_kid(kid_id)
        if kid:
            self.name_lbl.setText(kid['name'])
            self.bal_lbl.setText(f"${kid['balance']:.2f}")
            self.lbl_title.setText(f"{kid['name'].upper()} // DASHBOARD")
            
            # Progress
            summary = kid.get("chores_summary", {})
            total = summary.get("total_weight", 1)
            if total == 0: total = 1 # Avoid div zero
            
            # Official (Approved)
            off_pct = summary.get("week_pct", 0)
            self.prog_official.setValue(off_pct)
            
            # Kid (Completed + Approved)
            done_weight = summary.get("completed_weight", 0)
            kid_pct = int((done_weight / total) * 100)
            if kid_pct > 100: kid_pct = 100
            self.prog_kid.setValue(kid_pct)
        
        self.load_chores()

    def load_chores(self):
        # Clear existing
        while self.scroll_layout.count():
            w = self.scroll_layout.takeAt(0).widget()
            if w: w.setParent(None)
            
        chores = ApiService.get_kid_chores(self.kid_id)
        
        # Add labels
        if not chores:
            self.scroll_layout.addWidget(QLabel("NO ACTIVE QUESTS DETECTED."))
            return

        # Separate Daily/Weekly
        dailies = [c for c in chores if c.get("frequency") == "DAILY"]
        weeklies = [c for c in chores if c.get("frequency") == "WEEKLY"]
        
        if dailies:
            self.scroll_layout.addWidget(self._make_section_header("DAILY QUESTS"))
            for c in dailies:
                self.scroll_layout.addWidget(self._create_quest_row(c))
                
        if weeklies:
            self.scroll_layout.addWidget(self._make_section_header("WEEKLY QUESTS"))
            for c in weeklies:
                self.scroll_layout.addWidget(self._create_quest_row(c))

    def _make_section_header(self, text):
        l = QLabel(text)
        l.setStyleSheet("color: #00E5FF; font-weight: bold; margin-top: 10px; border-bottom: 1px solid #007BFF;")
        return l

    def _create_quest_row(self, c):
        # A row looking like a mini-quest entry
        # Replacing simple frame with a styled QFrame that looks techy
        frame = QFrame()
        frame.setStyleSheet("background-color: rgba(0, 123, 255, 0.1); border: 1px solid #007BFF; border-radius: 4px;")
        layout = QHBoxLayout(frame)
        
        # Info
        v = QVBoxLayout()
        name = QLabel(c['name'])
        name.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        v.addWidget(name)
        
        desc = QLabel(c.get('description', ''))
        desc.setStyleSheet("color: #B0BEC5; font-size: 14px;")
        v.addWidget(desc)
        layout.addLayout(v)
        
        layout.addStretch()
        
        # Action
        status = c.get('status', 'INCOMPLETE')
        
        # Logic: 
        # INCOMPLETE -> Show "COMPLETE" button
        # PENDING -> Show "PENDING APPROVAL" label (Yellow)
        # APPROVED -> Show "APPROVED" label (Green)
        # REJECTED -> Show "REJECTED" label (Red)

        if status == 'INCOMPLETE':
            btn = HoloButton("COMPLETE", is_primary=True)
            btn.setFixedSize(145, 40)  # FIX: Was 120, increased to 145 for full text
            btn.clicked.connect(lambda _, cid=c['id']: self.mark_done(cid))
            layout.addWidget(btn)
        elif status == 'REJECTED':
            # RETRY Flow
            btn = HoloButton("RETRY", is_primary=False)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 85, 85, 0.2);
                    border: 1px solid #FF5555;
                    color: #FF5555;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: rgba(255, 85, 85, 0.4);
                }
            """)
            btn.setFixedSize(140, 40)
            btn.clicked.connect(lambda _, cid=c['id']: self.mark_done(cid)) # Resubmit
            layout.addWidget(btn)
        else:
            lbl_text = status
            lbl_style = "font-weight: bold; color: white;"
            
            if status == "PENDING":
                lbl_text = "WAITING APPROVAL"
                lbl_style = "color: #FFD700; font-weight: bold;" # Gold
            elif status == "APPROVED":
                lbl_text = "COMPLETED"
                lbl_style = "color: #00E5FF; font-weight: bold;" # Cyan

            lbl = QLabel(lbl_text)
            lbl.setStyleSheet(lbl_style)
            layout.addWidget(lbl)
            
        return frame

    def mark_done(self, chore_id):
        ApiService.complete_chore(chore_id, self.kid_id)
        self.load_chores() # Refresh
