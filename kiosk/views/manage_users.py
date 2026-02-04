from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QListWidget, QListWidgetItem, QLineEdit, QFormLayout)
from PySide6.QtCore import Signal, Qt
from ..components.holo_widgets import HoloButton, HoloFrame
from ..components.holo_keyboard import HoloLineEdit
from ..components.holo_alert import HoloAlert
from ..services.api import ApiService

class ManageUsersView(QWidget):
    back_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.users = []
        self.selected_user = None # None means "New User" mode

        main = QVBoxLayout(self)
        
        # Header
        top = QHBoxLayout()
        btn_back = HoloButton("← BACK", is_primary=False)
        btn_back.setFixedSize(120, 50)
        btn_back.clicked.connect(self.back_clicked.emit)
        top.addWidget(btn_back)
        
        lbl_title = QLabel("MANAGE CREW")
        lbl_title.setObjectName("HoloHeader")
        top.addWidget(lbl_title)
        top.addStretch()
        main.addLayout(top)

        # Content Split
        content = QHBoxLayout()
        
        # Content Layout Adjustment
        # LEFT Panel
        left_panel = HoloFrame("CREW ROSTER")
        left_panel.setFixedWidth(300)
        ll = QVBoxLayout(left_panel)
        # Increased top margin to 90 for clearance, Bottom 40 to align buttons with Right Panel
        ll.setContentsMargins(20, 90, 20, 40)
        
        # ... list widget setup ...
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: none;
                color: white;
                font-size: 20px;
                outline: none;
            }
            QListWidget::item {
                padding: 20px 15px;
                border-bottom: 1px solid rgba(0, 229, 255, 0.3);
                margin-bottom: 5px;
                min-height: 60px;
            }
            QListWidget::item:selected {
                background: rgba(0, 229, 255, 0.2);
                color: #00E5FF;
                border-left: 4px solid #00E5FF;
            }
        """)
        self.list_widget.itemClicked.connect(self.on_user_selected)
        ll.addWidget(self.list_widget)
        
        # Spacing before Add button
        ll.addSpacing(10)
        
        btn_add = HoloButton("ADD RECRUIT")
        btn_add.clicked.connect(self.on_add_clicked)
        ll.addWidget(btn_add)
        
        content.addWidget(left_panel)
        
        # RIGHT Panel
        right_panel = HoloFrame("PERSONNEL FILE")
        rl = QVBoxLayout(right_panel)
        # Increased top margin to 100 for more header clearance
        rl.setContentsMargins(40, 100, 40, 40)
        
        self.form_layout = QFormLayout()
        self.form_layout.setSpacing(25)
        self.form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.inp_name = HoloLineEdit()
        self.inp_name.setPlaceholderText("Enter Name")
        # self.style_input(self.inp_name) # Internal style used
        self.form_layout.addRow(self.make_label("NAME:"), self.inp_name)
        
        self.inp_allowance = HoloLineEdit()
        self.inp_allowance.setPlaceholderText("0")
        # self.style_input(self.inp_allowance)
        self.form_layout.addRow(self.make_label("ALLOWANCE ($):"), self.inp_allowance)
        
        rl.addLayout(self.form_layout)
        rl.addStretch()
        
        # Actions
        actions = QHBoxLayout()
        
        # Delete Button (Hidden by default)
        self.btn_delete = HoloButton("DELETE", is_primary=False)
        self.btn_delete.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 50, 50, 0.2);
                border: 1px solid #FF5555;
                color: #FF5555;
            }
            QPushButton:hover {
                background-color: rgba(255, 50, 50, 0.4);
            }
        """)
        self.btn_delete.setFixedSize(120, 60)
        self.btn_delete.clicked.connect(self.delete_user)
        self.btn_delete.hide()
        actions.addWidget(self.btn_delete)
        
        actions.addStretch()
        
        self.btn_save = HoloButton("SAVE RECORD")
        self.btn_save.setFixedSize(200, 60)
        self.btn_save.clicked.connect(self.save_user)
        actions.addWidget(self.btn_save)
        
        rl.addLayout(actions)
        
        content.addWidget(right_panel)
        main.addLayout(content)
        
        # Initial Load
        self.refresh_list()

    def showEvent(self, event):
        self.refresh_list()
        super().showEvent(event)

    def style_input(self, widget):
        widget.setStyleSheet("""
            QLineEdit {
                background: rgba(0, 0, 0, 0.5);
                border: 1px solid #007BFF;
                color: #00E5FF;
                padding: 12px;
                font-size: 20px;
                border-radius: 4px;
            }
            QLineEdit:focus {
                border: 1px solid #00E5FF;
                background: rgba(0, 229, 255, 0.1);
            }
        """)
        
    def make_label(self, text):
        l = QLabel(text)
        l.setStyleSheet("color: white; font-weight: bold; font-size: 16px;")
        return l

    def refresh_list(self):
        self.list_widget.clear()
        self.users = ApiService.get_kids()
        
        for u in self.users:
            name = u.get("name", "Unknown")
            balance = u.get("balance", 0.0)
            # Display name and balance on separate lines
            item = QListWidgetItem(f"{name}\n${balance:.2f}")
            item.setData(Qt.ItemDataRole.UserRole, u)
            self.list_widget.addItem(item)
            
    def on_user_selected(self, item):
        data = item.data(Qt.ItemDataRole.UserRole)
        self.selected_user = data
        self.inp_name.setText(data.get("name", ""))
        self.inp_allowance.setText(str(data.get("allowance", 0.0)))
        self.btn_save.setText("UPDATE RECORD")
        self.btn_delete.show()

    def on_add_clicked(self):
        self.list_widget.clearSelection()
        self.selected_user = None
        self.inp_name.clear()
        self.inp_allowance.clear()
        self.btn_save.setText("CREATE RECORD")
        self.btn_delete.hide()
        self.inp_name.setFocus()

    def save_user(self):
        name = self.inp_name.text().strip()
        if not name:
            HoloAlert("VALIDATION ERROR", "Name cannot be empty.", self.window(), is_error=True).exec()
            return
        
        try:
            allowance = float(self.inp_allowance.text().strip() or "0")
        except ValueError:
            HoloAlert("VALIDATION ERROR", "Allowance must be a valid number.", self.window(), is_error=True).exec()
            return
            
        if self.selected_user:
            # Update
            kid_id = self.selected_user["id"]
            result = ApiService.update_kid(kid_id, name, allowance)
            if result:
                HoloAlert("SUCCESS", f"Updated {name}", self.window()).exec()
            else:
                HoloAlert("ERROR", "Failed to update crew member.", self.window(), is_error=True).exec()
        else:
            # Create
            result = ApiService.create_kid(name, allowance)
            if result:
                HoloAlert("SUCCESS", f"Recruited {name}!", self.window()).exec()
            else:
                HoloAlert("ERROR", "Failed to create crew member. Check backend logs.", self.window(), is_error=True).exec()
            
        self.refresh_list()
        self.on_add_clicked() # Reset form

    def delete_user(self):
        if self.selected_user:
            kid_id = self.selected_user["id"]
            ApiService.delete_kid(kid_id)
            self.refresh_list()
            self.on_add_clicked()
