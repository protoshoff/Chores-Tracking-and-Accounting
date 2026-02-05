from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QListWidget, QListWidgetItem, QLineEdit, QFormLayout,
                               QComboBox, QSpinBox)
from PySide6.QtCore import Signal, Qt
from ..components.holo_widgets import HoloButton, HoloFrame
from ..components.holo_keyboard import HoloLineEdit
from ..services.api import ApiService

class ManageChoresView(QWidget):
    back_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.chores = []
        self.kids = []
        self.selected_chore = None 

        main = QVBoxLayout(self)
        
        # Header
        top = QHBoxLayout()
        btn_back = HoloButton("← BACK", is_primary=False)
        btn_back.setFixedSize(120, 50)
        btn_back.clicked.connect(self.back_clicked.emit)
        top.addWidget(btn_back)
        
        lbl_title = QLabel("MANAGE QUESTS")
        lbl_title.setObjectName("HoloHeader")
        top.addWidget(lbl_title)
        top.addStretch()
        main.addLayout(top)

        # Content Split
        content = QHBoxLayout()
        
        # --- LEFT: Chore List ---
        left_panel = HoloFrame("ACTIVE QUESTS")
        left_panel.setFixedWidth(350) 
        ll = QVBoxLayout(left_panel)
        # Using the tuned margins from manage_users
        ll.setContentsMargins(20, 90, 20, 40)
        
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: none;
                color: white;
                font-size: 18px;
                outline: none;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid rgba(0, 229, 255, 0.3);
            }
            QListWidget::item:selected {
                background: rgba(0, 229, 255, 0.2);
                color: #00E5FF;
                border-left: 4px solid #00E5FF;
            }
        """)
        self.list_widget.itemClicked.connect(self.on_chore_selected)
        ll.addWidget(self.list_widget)
        
        ll.addSpacing(10)
        
        btn_add = HoloButton("NEW QUEST")
        btn_add.clicked.connect(self.on_add_clicked)
        ll.addWidget(btn_add)
        
        content.addWidget(left_panel)
        
        # --- RIGHT: Form ---
        right_panel = HoloFrame("QUEST DETAILS")
        rl = QVBoxLayout(right_panel)
        rl.setContentsMargins(40, 100, 40, 40)
        
        self.form_layout = QFormLayout()
        self.form_layout.setSpacing(20)
        self.form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        # Name
        self.inp_name = HoloLineEdit()
        self.inp_name.setPlaceholderText("Quest Name")
        # self.style_input(self.inp_name)
        self.form_layout.addRow(self.make_label("NAME:"), self.inp_name)
        
        # Description
        self.inp_desc = HoloLineEdit()
        self.inp_desc.setPlaceholderText("Brief description")
        # self.style_input(self.inp_desc)
        self.form_layout.addRow(self.make_label("BRIEFING:"), self.inp_desc)
        
        # Assignee
        self.combo_kid = QComboBox()
        self.style_combo(self.combo_kid)
        self.form_layout.addRow(self.make_label("ASSIGN TO:"), self.combo_kid)
        
        # Frequency
        self.combo_freq = QComboBox()
        self.style_combo(self.combo_freq)
        self.combo_freq.addItems(["DAILY", "WEEKLY"])
        self.combo_freq.currentIndexChanged.connect(self.on_freq_changed)
        self.form_layout.addRow(self.make_label("FREQUENCY:"), self.combo_freq)
        
        # Due Day (Hidden unless Weekly)
        self.lbl_day = self.make_label("DUE DAY:")
        self.combo_day = QComboBox()
        self.style_combo(self.combo_day)
        self.combo_day.addItems(["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"])
        self.form_layout.addRow(self.lbl_day, self.combo_day)
        self.combo_day.hide()
        self.lbl_day.hide()
        
        # Weight
        self.spin_weight = QSpinBox()
        self.spin_weight.setRange(1, 10)
        self.spin_weight.setFixedWidth(100) # Safe width for visibility
        self.style_spin(self.spin_weight)
        self.form_layout.addRow(self.make_label("XP WEIGHT (1-10):"), self.spin_weight)
        
        rl.addLayout(self.form_layout)
        rl.addStretch()
        
        # Actions
        actions = QHBoxLayout()
        
        self.btn_delete = HoloButton("ARCHIVE", is_primary=False)
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
        self.btn_delete.clicked.connect(self.archive_chore)
        self.btn_delete.hide()
        actions.addWidget(self.btn_delete)
        
        actions.addStretch()
        
        self.btn_save = HoloButton("SAVE QUEST")
        self.btn_save.setFixedSize(200, 60)
        self.btn_save.clicked.connect(self.save_chore)
        actions.addWidget(self.btn_save)
        
        rl.addLayout(actions)
        
        content.addWidget(right_panel)
        main.addLayout(content)
        
        # Initial Load
        self.refresh_data()

    def showEvent(self, event):
        self.refresh_data()
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
        
    def style_combo(self, widget):
        widget.setStyleSheet("""
            QComboBox {
                background: rgba(0, 0, 0, 0.5);
                border: 1px solid #007BFF;
                color: #00E5FF;
                padding: 10px;
                font-size: 18px;
                border-radius: 4px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 40px;
                border-left-width: 1px;
                border-left-color: #007BFF;
                border-left-style: solid;
                background: #001133;
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px;
            }
            QComboBox::down-arrow {
                image: url(kiosk/assets/arrow_down.svg);
                width: 24px; 
                height: 24px;
                subcontrol-position: center;
            }
             QComboBox QAbstractItemView {
                background: #000;
                color: #00E5FF;
                selection-background-color: #007BFF;
                border: 1px solid #007BFF;
            }
        """)

    def style_spin(self, widget):
        widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        widget.setStyleSheet("""
            QSpinBox {
                qproperty-alignment: AlignCenter;
                background: rgba(0, 0, 0, 0.5);
                border: 1px solid #007BFF;
                color: #00E5FF;
                padding-top: 5px;
                padding-bottom: 5px;
                padding-left: 0px; 
                padding-right: 30px; /* Exact width of buttons */
                font-size: 20px;
                border-radius: 4px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 30px;
                background: #001133;
                border-left: 1px solid #007BFF;
            }
            QSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                border-bottom: 1px solid #007BFF;
                border-top-right-radius: 4px;
            }
            QSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                border-bottom-right-radius: 4px;
            }
            QSpinBox::up-arrow {
                image: url(kiosk/assets/arrow_up.svg);
                width: 24px; height: 24px;
                subcontrol-position: center;
            }
            QSpinBox::down-arrow {
                image: url(kiosk/assets/arrow_down.svg);
                width: 24px; height: 24px;
                subcontrol-position: center;
            }
        """)

    def make_label(self, text):
        l = QLabel(text)
        l.setStyleSheet("color: white; font-weight: bold; font-size: 16px;")
        return l

    def refresh_data(self):
        # 1. Fetch Kids for Dropdown
        self.kids = ApiService.get_kids()
        self.combo_kid.clear()
        for k in self.kids:
            self.combo_kid.addItem(k.get("name", "Unknown"), k.get("id"))
            
        # 2. Fetch All Chores
        self.list_widget.clear()
        self.chores = []
        
        for k in self.kids:
            kid_chores = ApiService.get_kid_chores(k["id"])
            for c in kid_chores:
                c["kid_name"] = k["name"] # Attach name for display
                self.chores.append(c)
                
                # Add to List
                label = f"[{k['name']}] {c['name']}"
                item = QListWidgetItem(label)
                item.setData(Qt.ItemDataRole.UserRole, c)
                self.list_widget.addItem(item)
    
    def on_chore_selected(self, item):
        data = item.data(Qt.ItemDataRole.UserRole)
        self.selected_chore = data
        
        self.inp_name.setText(data.get("name", ""))
        self.inp_desc.setText(data.get("description", ""))
        self.spin_weight.setValue(data.get("weight", 1))
        
        idx = self.combo_freq.findText(freq)
        if idx >= 0: self.combo_freq.setCurrentIndex(idx)
        
        # Set Due Day
        due_day = data.get("due_day")
        if due_day is not None:
            self.combo_day.setCurrentIndex(due_day)
        else:
            self.combo_day.setCurrentIndex(0)
            
        self.on_freq_changed() # Update visibility
        
        target_kid_name = data.get("kid_name")
        for i in range(self.combo_kid.count()):
            if self.combo_kid.itemText(i) == target_kid_name:
                self.combo_kid.setCurrentIndex(i)
                break
                
        self.btn_save.setText("UPDATE QUEST")
        self.btn_delete.show()

    def on_add_clicked(self):
        self.list_widget.clearSelection()
        self.selected_chore = None
        self.inp_name.clear()
        self.inp_desc.clear()
        self.spin_weight.setValue(1)
        self.combo_freq.setCurrentIndex(0)
        self.combo_day.setCurrentIndex(0)
        self.on_freq_changed()
        
        self.btn_save.setText("CREATE QUEST")
        self.btn_delete.hide()
        self.inp_name.setFocus()

    def save_chore(self):
        name = self.inp_name.text().strip()
        if not name: return 
        
        desc = self.inp_desc.text().strip()
        weight = self.spin_weight.value()
        freq = self.combo_freq.currentText()
        kid_id = self.combo_kid.currentData()
        
        due_day = None
        if freq == "WEEKLY":
            due_day = self.combo_day.currentIndex()
        
        if self.selected_chore:
            # Update
            cid = self.selected_chore["id"]
            ApiService.update_chore(cid, name=name, description=desc, weight=weight, frequency=freq, due_day=due_day)
        else:
            # Create
            if kid_id is not None:
                ApiService.create_chore(kid_id, name, description=desc, reward=weight, frequency=freq, due_day=due_day)
            
        self.refresh_data()
        self.on_add_clicked()

    def on_freq_changed(self):
        freq = self.combo_freq.currentText()
        if freq == "WEEKLY":
            self.lbl_day.show()
            self.combo_day.show()
        else:
            self.lbl_day.hide()
            self.combo_day.hide() 

    def archive_chore(self):
        if self.selected_chore:
            cid = self.selected_chore["id"]
            ApiService.delete_chore(cid)
            self.refresh_data()
            self.on_add_clicked()
