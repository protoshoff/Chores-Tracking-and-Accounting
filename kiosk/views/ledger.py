from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QTableWidget, QTableWidgetItem, QHeaderView, QFrame)
from PySide6.QtCore import Qt, Signal
from ..components.holo_widgets import HoloButton, HoloFrame
from ..components.holo_alert import HoloAlert
from ..components.holo_keyboard import HoloKeyboard
from ..services.api import ApiService

class LedgerView(QWidget):
    back_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.kid_id = None
        
        main = QVBoxLayout(self)
        
        # --- Header ---
        top = QHBoxLayout()
        btn_back = HoloButton("← BACK", is_primary=False)
        btn_back.setFixedSize(120, 50)
        btn_back.clicked.connect(self.back_clicked.emit)
        top.addWidget(btn_back)
        
        self.lbl_title = QLabel("LEDGER & PAYOUTS")
        self.lbl_title.setObjectName("HoloHeader")
        top.addWidget(self.lbl_title)
        top.addStretch()
        main.addLayout(top)
        
        # --- Content ---
        content = QHBoxLayout()
        
        # LEFT: Kid Stats & Actions
        left_panel = QFrame()
        left_panel.setFixedWidth(350)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0,0,0,0)
        left_layout.setSpacing(20)
        
        self.card_frame = HoloFrame("CURRENT BALANCE")
        cf_layout = QVBoxLayout(self.card_frame)
        self.lbl_balance = QLabel("$0.00")
        self.lbl_balance.setStyleSheet("font-size: 48px; color: #00E5FF; font-weight: bold;")
        self.lbl_balance.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cf_layout.addWidget(self.lbl_balance)
        left_layout.addWidget(self.card_frame)
        
        # Actions
        btn_add = HoloButton("ADD FUNDS (+)")
        btn_add.clicked.connect(lambda: self.adjust_funds(1))
        left_layout.addWidget(btn_add)
        
        btn_sub = HoloButton("DEDUCT FUNDS (-)")
        btn_sub.clicked.connect(lambda: self.adjust_funds(-1))
        left_layout.addWidget(btn_sub)
        
        left_layout.addStretch()
        
        btn_payout = HoloButton("PAYOUT ALL")
        btn_payout.setStyleSheet("background-color: rgba(0, 255, 0, 50); border: 2px solid #00FF00; color: #00FF00;")
        btn_payout.clicked.connect(self.do_payout)
        left_layout.addWidget(btn_payout)
        
        content.addWidget(left_panel)
        
        # RIGHT: History Table
        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)
        
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["DATE", "DESC", "AMOUNT", "ID"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) # Desc stretches
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setColumnHidden(3, True) # Hide ID
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: rgba(0, 20, 40, 150);
                gridline-color: #00E5FF;
                color: white;
                font-size: 16px;
            }
            QHeaderView::section {
                background-color: #003344;
                color: #00E5FF;
                padding: 5px;
            }
        """)
        right_layout.addWidget(self.table)
        
        btn_del = HoloButton("DELETE SELECTED ENTRY", is_primary=False)
        btn_del.clicked.connect(self.delete_selected)
        right_layout.addWidget(btn_del)
        
        content.addWidget(right_panel)
        main.addLayout(content)
        
    def load_kid(self, kid_id):
        self.kid_id = kid_id
        self.refresh()
        
    def refresh(self):
        if not self.kid_id: return
        
        # Update Balance (Get kid details first ideally, but history has it?)
        # Let's verify kid specifically or just rely on API for history
        
        # Get History
        history = ApiService.get_ledger_history(self.kid_id)
        
        # Update Table
        self.table.setRowCount(len(history))
        balance_cents = 0 # If we fetched user we'd have it. 
        # Actually, let's just refetch 'get_kids' to find this kid's balance? 
        # Or better: Add 'get_kid(id)' to API. For now, let's loop kids.
        
        kids = ApiService.get_kids()
        for k in kids:
            if k["id"] == self.kid_id:
                self.lbl_title.setText(f"LEDGER: {k['name'].upper()}")
                self.lbl_balance.setText(f"${k['balance_cents']/100:.2f}")
                break
        
        for r, entry in enumerate(history):
            dt = entry["timestamp"].split("T")[0]
            amt = entry["amount_cents"] / 100
            desc = entry["description"]
            
            # Format Amount
            amt_str = f"${amt:.2f}"
            if amt > 0: amt_str = f"+{amt_str}"
            
            item_date = QTableWidgetItem(dt)
            item_desc = QTableWidgetItem(desc)
            item_amt = QTableWidgetItem(amt_str)
            item_id = QTableWidgetItem(str(entry["id"]))
            
            # Colors
            if amt < 0:
                item_amt.setForeground(Qt.GlobalColor.red)
            else:
                item_amt.setForeground(Qt.GlobalColor.green)
                
            self.table.setItem(r, 0, item_date)
            self.table.setItem(r, 1, item_desc)
            self.table.setItem(r, 2, item_amt)
            self.table.setItem(r, 3, item_id)
            
    def adjust_funds(self, sign):
        # 1. Ask Amount
        dlg = HoloKeyboard(self.window(), "", title="ENTER AMOUNT ($)")
        if dlg.exec():
            txt = dlg.get_text()
            try:
                val = float(txt)
                cents = int(val * 100)
                if cents <= 0: raise ValueError
                
                # 2. Ask Description
                dlg_desc = HoloKeyboard(self.window(), "", title="ENTER REASON")
                desc = "Manual Adjustment"
                if dlg_desc.exec():
                    desc = dlg_desc.get_text() or desc
                    
                # 3. Send
                t_type = "BONUS" if sign > 0 else "SPEND"
                success = ApiService.add_transaction(self.kid_id, cents * sign, t_type, desc)
                if success:
                    self.refresh()
                else:
                    HoloAlert("ERROR", "Failed to add transaction.", self.window(), is_error=True).exec()
                    
            except ValueError:
                HoloAlert("INVALID", "Please enter a valid number.", self.window(), is_error=True).exec()

    def do_payout(self):
        # Confirm
        # We don't have a Yes/No dialog yet, let's use HoloAlert with a hack or just trust it?
        # Let's quick-add confirmation logic?
        # For v0.1 polish, let's trust the button press or maybe reuse text input "TYPE 'YES'"?
        # Let's make it simple: Just do it.
        
        success = ApiService.payout_kid(self.kid_id)
        if success:
             HoloAlert("PAYOUT SUCCESSFUL", "Balance reset to $0.00", self.window()).exec()
             self.refresh()
        else:
             HoloAlert("ERROR", "Payout failed (Zero balance?)", self.window(), is_error=True).exec()
             
    def delete_selected(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows: return
        
        row = rows[0].row()
        item_id = self.table.item(row, 3)
        if not item_id: return
        
        entry_id = int(item_id.text())
        success = ApiService.delete_transaction(entry_id)
        if success:
            self.refresh()
        else:
            HoloAlert("ERROR", "Delete failed", self.window(), is_error=True).exec()
