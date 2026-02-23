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
        
        # Add Refresh Button
        btn_refresh = HoloButton("↻ REFRESH", is_primary=False)
        btn_refresh.setFixedSize(150, 50)
        btn_refresh.clicked.connect(self.refresh)
        top.addWidget(btn_refresh)
        
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
        cf_layout.setContentsMargins(10, 70, 10, 20) # Top 70 to clear 60px Title
        self.lbl_balance = QLabel("$0.00")
        self.lbl_balance.setObjectName("HoloHeader") # Use theme font
        self.lbl_balance.setStyleSheet("font-size: 48px;") # Override size only
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
        
        # Add status label for loading/error messages
        self.lbl_status = QLabel()
        self.lbl_status.setStyleSheet("color: #888; font-size: 14px; padding: 5px;")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(self.lbl_status)
        
        btn_del = HoloButton("DELETE SELECTED ENTRY", is_primary=False)
        btn_del.clicked.connect(self.delete_selected)
        right_layout.addWidget(btn_del)
        
        content.addWidget(right_panel)
        main.addLayout(content)
        
    def load_kid(self, kid_id):
        self.kid_id = kid_id
        self.refresh()
        
    def refresh(self):
        """Refresh ledger data from API with error handling"""
        if not self.kid_id:
            return
        
        try:
            # Show loading status
            self.lbl_status.setText("Loading...")
            self.lbl_status.setStyleSheet("color: #00E5FF; font-size: 14px; padding: 5px;")
            
            # Get History
            history = ApiService.get_ledger_history(self.kid_id)
            
            if history is None:
                # API returned None (error condition)
                self.lbl_status.setText("⚠ Error loading transactions")
                self.lbl_status.setStyleSheet("color: #FF5555; font-size: 14px; padding: 5px;")
                return
            
            # Update Table
            self.table.setRowCount(len(history))
            
            # Get current balance from kid data
            kids = ApiService.get_kids()
            kid_found = False
            for k in kids:
                if k["id"] == self.kid_id:
                    self.lbl_title.setText(f"LEDGER: {k['name'].upper()}")
                    self.lbl_balance.setText(f"${k['balance']:.2f}")
                    kid_found = True
                    break
            
            if not kid_found:
                self.lbl_status.setText("⚠ Kid not found")
                self.lbl_status.setStyleSheet("color: #FF5555; font-size: 14px; padding: 5px;")
                return
            
            # Populate table
            for r, entry in enumerate(history):
                try:
                    dt = entry.get("timestamp", "").split("T")[0]
                    amt = entry.get("amount", 0)
                    desc = entry.get("description", "N/A")
                    
                    # Format Amount
                    amt_str = f"${amt:.2f}"
                    if amt > 0:
                        amt_str = f"+{amt_str}"
                    
                    item_date = QTableWidgetItem(dt)
                    item_desc = QTableWidgetItem(desc)
                    item_amt = QTableWidgetItem(amt_str)
                    item_id = QTableWidgetItem(str(entry.get("id", "")))
                    
                    # Colors
                    if amt < 0:
                        item_amt.setForeground(Qt.GlobalColor.red)
                    else:
                        item_amt.setForeground(Qt.GlobalColor.green)
                        
                    self.table.setItem(r, 0, item_date)
                    self.table.setItem(r, 1, item_desc)
                    self.table.setItem(r, 2, item_amt)
                    self.table.setItem(r, 3, item_id)
                except Exception as e:
                    print(f"Error processing ledger entry: {e}")
                    continue
            
            # Update status with success
            from datetime import datetime
            now = datetime.now().strftime("%I:%M %p")
            self.lbl_status.setText(f"✓ Updated {now}")
            self.lbl_status.setStyleSheet("color: #00FF00; font-size: 14px; padding: 5px;")
            
        except Exception as e:
            print(f"Error in ledger refresh: {e}")
            self.lbl_status.setText(f"⚠ Error: {str(e)[:50]}")
            self.lbl_status.setStyleSheet("color: #FF5555; font-size: 14px; padding: 5px;")
            
    def adjust_funds(self, sign):
        """Add or deduct funds with improved validation"""
        # 1. Ask Amount
        dlg = HoloKeyboard(self.window(), "", title="ENTER AMOUNT ($)")
        if dlg.exec():
            txt = dlg.get_text().strip()
            if not txt:
                return
            
            try:
                val = float(txt)
                
                # Validation
                if val <= 0:
                    HoloAlert("INVALID", "Amount must be greater than zero.", 
                             self.window(), is_error=True).exec()
                    return
                
                if val > 10000:
                    HoloAlert("INVALID", "Amount too large (max $10,000).", 
                             self.window(), is_error=True).exec()
                    return
                
                # 2. Ask Description
                dlg_desc = HoloKeyboard(self.window(), "", title="ENTER REASON")
                desc = "Manual Adjustment"
                if dlg_desc.exec():
                    desc = dlg_desc.get_text() or desc
                    
                # 3. Send
                t_type = "BONUS" if sign > 0 else "SPEND"
                success = ApiService.add_transaction(self.kid_id, val * sign, t_type, desc)
                
                if success:
                    HoloAlert("SUCCESS", f"Transaction added: ${val * sign:.2f}", 
                             self.window()).exec()
                    self.refresh()
                else:
                    HoloAlert("ERROR", "Failed to add transaction. Check backend connection.", 
                             self.window(), is_error=True).exec()
                    
            except ValueError:
                HoloAlert("INVALID", "Please enter a valid number.", 
                         self.window(), is_error=True).exec()

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
