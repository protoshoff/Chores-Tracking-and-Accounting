from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QScrollArea, QMessageBox
from PySide6.QtCore import Signal, Qt
import requests
from ..components.holo_widgets import HoloButton, HoloFrame

class ApprovalQueueView(QWidget):
    back_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        
        main = QVBoxLayout(self)
        
        # Header
        top = QHBoxLayout()
        btn_back = HoloButton("← BACK", is_primary=False)
        btn_back.setFixedSize(120, 50)
        btn_back.clicked.connect(self.back_clicked.emit)
        top.addWidget(btn_back)
        
        lbl_title = QLabel("MISSION CONTROL") # Renamed from "Pending Approvals" to fit theme
        lbl_title.setObjectName("HoloHeader") 
        top.addWidget(lbl_title)
        top.addStretch()
        main.addLayout(top)
        
        # List Container
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        self.container_widget = QWidget()
        self.container_widget.setStyleSheet("background: transparent;")
        
        self.list_layout = QVBoxLayout(self.container_widget)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self.container_widget)
        main.addWidget(scroll)
        
    def refresh(self):
        # Clear
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            widget = item.widget()
            if widget: widget.setParent(None)
            
        try:
            resp = requests.get("http://localhost:8000/api/approvals/pending")
            if resp.status_code == 200:
                pending = resp.json()
            else:
                pending = []
        except:
             pending = []
             
        if not pending:
            lbl = QLabel("NO PENDING AUTHORIZATIONS DETECTED.")
            lbl.setStyleSheet("color: #AAA; font-size: 18px;")
            self.list_layout.addWidget(lbl)
            return

        # Group by Date
        from datetime import datetime
        
        # Sort pending by date descending (Newest first)
        pending.sort(key=lambda x: x['date'], reverse=True)
        
        current_date_header = None
        
        for p in pending:
            # Check date header
            p_date = p['date'].split("T")[0] # ISO string prefix
            if p_date != current_date_header:
                current_date_header = p_date
                # Create Header
                header = QLabel(f"📅 {p_date}")
                header.setStyleSheet("color: #00E5FF; font-size: 20px; font-weight: bold; margin-top: 20px; border-bottom: 2px solid #00E5FF;")
                self.list_layout.addWidget(header)
                
            row = self._create_row(p)
            self.list_layout.addWidget(row)
            
    def _create_row(self, item):
        # Sci-Fi Row using HoloFrame-like style or QFrame with border
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 123, 255, 0.1); 
                border: 1px solid #00E5FF; 
                border-radius: 4px; 
                margin-bottom: 10px;
            }
        """)
        
        # Main Layout: Horizontal
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(20, 10, 20, 10)
        
        # -- Info Block (Vertical) --
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)
        
        # Kid Name - Chore Name
        # "GRAYSON: WALK DOG"
        title_txt = f"{item.get('kid_name', 'UNKNOWN').upper()}: {item.get('chore_name', 'UNKNOWN').upper()}"
        lbl_title = QLabel(title_txt)
        lbl_title.setStyleSheet("font-size: 22px; font-weight: bold; color: white; border: none; background: transparent;")
        info_layout.addWidget(lbl_title)
        
        # Date / Subtext
        sub_txt = f"Submitted: {item.get('date')} • Waiting Auth"
        lbl_sub = QLabel(sub_txt)
        lbl_sub.setStyleSheet("font-size: 14px; color: #00E5FF; border: none; background: transparent;")
        info_layout.addWidget(lbl_sub)
        
        layout.addLayout(info_layout)
        
        layout.addStretch()
        
        # -- Actions --
        
        # Approve (Green - matching Reject button's perfect style)
        btn_approve = HoloButton("APPROVE")
        btn_approve.setStyleSheet("""
            QPushButton {
                border: 1px solid #00FF66;
                color: #00FF66;
                background-color: rgba(0, 255, 100, 0.2);
            }
            QPushButton:hover {
                background-color: #00FF66;
                color: #000;
            }
        """)
        btn_approve.setFixedSize(155, 50)  # FIX: Was 140, increased to 155 for full "APPROVE" text
        btn_approve.clicked.connect(lambda: self.review_action(item['id'], "APPROVE"))
        layout.addWidget(btn_approve)
        
        layout.addSpacing(10)
        
        # Reject (Red - RESTORED original perfect styling)
        btn_reject = HoloButton("REJECT", is_primary=False)
        btn_reject.setStyleSheet("""
            QPushButton {
                border: 1px solid #FF5555;
                color: #FF5555;
                background-color: rgba(255, 50, 50, 0.2);
            }
            QPushButton:hover {
                background-color: #FF5555;
                color: #000;
            }
        """)
        btn_reject.setFixedSize(140, 50)
        btn_reject.clicked.connect(lambda: self.review_action(item['id'], "REJECT"))
        layout.addWidget(btn_reject)
        
        return frame

    def review_action(self, log_id, action):
        try:
             url = f"http://localhost:8000/api/approvals/{log_id}/review"
             requests.post(url, json={"action": action})
             self.refresh()
        except Exception as e:
            print(f"Error reviewing: {e}")
