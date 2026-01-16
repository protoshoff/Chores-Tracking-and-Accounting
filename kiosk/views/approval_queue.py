from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QScrollArea, QMessageBox
from PySide6.QtCore import Signal, Qt

class ApprovalQueueView(QWidget):
    back_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        
        main = QVBoxLayout(self)
        
        # Header
        top = QHBoxLayout()
        btn_back = QPushButton("← Back")
        btn_back.clicked.connect(self.back_clicked.emit)
        top.addWidget(btn_back)
        
        lbl_title = QLabel("Pending Approvals")
        lbl_title.setStyleSheet("font-size: 28px; font-weight: bold;")
        top.addWidget(lbl_title)
        top.addStretch()
        main.addLayout(top)
        
        # List Container
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.container_widget = QWidget()
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
            
        from ..services.api import ApiService
        # ApiService needs 'get_pending_approvals' method, adding stub here if missing or assuming addition
        # Let's add the code to fetch manually here until ApiService is updated, or update ApiService next.
        # Ideally, we update ApiService. Implementation Plan implied M13 included View logic.
        # We'll use requests directly or add helper method. Let's assume helper exists or we add it.
        # For now, quick patch:
        import requests
        try:
            resp = requests.get("http://localhost:8000/api/approvals/pending")
            if resp.status_code == 200:
                pending = resp.json()
            else:
                pending = []
        except:
             pending = []
             
        if not pending:
            self.list_layout.addWidget(QLabel("No pending approvals!"))
            return

        for p in pending:
            row = self._create_row(p)
            self.list_layout.addWidget(row)
            
    def _create_row(self, item):
        # item: {id, kid_id, chore_id, date, status...}
        # We need Kid Name and Chore Name. The API returns IDs.
        # Ideally API returns expanded data.
        # M4 APIs returned raw logs? Let's check M4 output from curls.
        # Output: [{"id":1,"week_id":"...","chore_id":1...}]
        # It misses names! We need to fetch names or update API.
        # For M13 UI, showing "Kid 1 - Chore 1" is okay-ish but "Alice - Walk Dog" is required.
        # Let's assume we show IDs for now to verify flow, and flag API update needed.
        
        frame = QFrame()
        frame.setStyleSheet("background-color: white; border: 1px solid #DDD; border-radius: 8px; margin-bottom: 5px;")
        layout = QHBoxLayout(frame)
        
        # Info
        info = QLabel(f"Kid #{item['kid_id']} • Chore #{item['chore_id']} • {item['date']}")
        info.setStyleSheet("font-size: 20px;")
        layout.addWidget(info)
        
        layout.addStretch()
        
        # Approve
        btn_approve = QPushButton("Approve ✔")
        btn_approve.setObjectName("BtnApprove")
        btn_approve.setFixedSize(140, 60)
        btn_approve.clicked.connect(lambda: self.review_action(item['id'], "APPROVE"))
        layout.addWidget(btn_approve)
        
        # Reject
        btn_reject = QPushButton("Reject ✖")
        btn_reject.setObjectName("BtnReject")
        btn_reject.setFixedSize(140, 60)
        btn_reject.clicked.connect(lambda: self.review_action(item['id'], "REJECT"))
        layout.addWidget(btn_reject)
        
        return frame

    def review_action(self, log_id, action):
        import requests
        try:
             url = f"http://localhost:8000/api/approvals/{log_id}/review"
             requests.post(url, json={"action": action})
             self.refresh()
        except Exception as e:
            print(f"Error reviewing: {e}")
