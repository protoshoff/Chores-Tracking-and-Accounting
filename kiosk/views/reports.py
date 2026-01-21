from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView
from PySide6.QtCore import Qt, Signal
from ..components.holo_widgets import HoloFrame, HoloButton
from ..services.api import ApiService

class ReportsView(QWidget):
    back_clicked = Signal()

    def __init__(self, parent=None):
        print("DEBUG: ReportsView start init")
        super().__init__(parent)
        
        main = QVBoxLayout(self)
        
        # Header
        top = QHBoxLayout()
        print("DEBUG: ReportsView creating HoloButton")
        btn_back = HoloButton("← BACK", is_primary=False)
        btn_back.setFixedSize(120, 50)
        btn_back.clicked.connect(self.back_clicked.emit)
        top.addWidget(btn_back)
        
        lbl = QLabel("MISSION REPORTS")
        lbl.setObjectName("HoloHeader")
        top.addWidget(lbl)
        top.addStretch()
        main.addLayout(top)
        
        # Table
        print("DEBUG: ReportsView creating QTableWidget")
        self.table = QTableWidget()
        print("DEBUG: ReportsView QTableWidget created")
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["WEEK", "RECRUIT", "TOTAL WGT", "DONE WGT", "PAYOUT"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        # Apply sci-fi style to table
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: rgba(10, 20, 30, 200);
                gridline-color: #00E5FF;
                color: #00E5FF;
                font-size: 18px;
                border: 2px solid #00E5FF;
            }
            QHeaderView::section {
                background-color: #050510;
                color: #FFD700;
                padding: 10px;
                border: 1px solid #00E5FF;
                font-weight: bold;
            }
        """)
        
        main.addWidget(self.table)
        print("DEBUG: ReportsView init finished")
        
    def showEvent(self, event):
        self.refresh_data()
        super().showEvent(event)
        
    def refresh_data(self):
        data = ApiService.get_rollups()
        self.table.setRowCount(0)
        
        if not data:
            return

        self.table.setRowCount(len(data))
        for row, item in enumerate(data):
            # item keys: week_id, kid_name, total_weight_possible, total_weight_completed, payout_cents
            week = item.get("week_id", "")
            name = item.get("kid_name", "Unknown")
            poss = str(item.get("total_weight_possible", 0))
            done = str(item.get("total_weight_completed", 0))
            payout = f"${item.get('payout', 0.0):.2f}"
            
            self.table.setItem(row, 0, QTableWidgetItem(week))
            self.table.setItem(row, 1, QTableWidgetItem(name))
            self.table.setItem(row, 2, QTableWidgetItem(poss))
            self.table.setItem(row, 3, QTableWidgetItem(done))
            self.table.setItem(row, 4, QTableWidgetItem(payout))
