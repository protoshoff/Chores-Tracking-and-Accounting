from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QListWidget, QListWidgetItem, QLineEdit, QFormLayout,
                               QComboBox, QSpinBox, QCheckBox)
from PySide6.QtCore import Signal, Qt
from datetime import date
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
        self.is_rotation_mode = False
        self.selected_rotation = None

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
        
        btn_add_rotation = HoloButton("NEW ROTATION")
        btn_add_rotation.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 107, 53, 0.2);
                border: 1px solid #FF6B35;
                color: #FF6B35;
            }
            QPushButton:hover {
                background-color: rgba(255, 107, 53, 0.4);
            }
        """)
        btn_add_rotation.clicked.connect(self.on_add_rotation_clicked)
        ll.addWidget(btn_add_rotation)
        
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
        
        # Weekdays Only checkbox (visible only for DAILY frequency)
        self.lbl_weekdays = self.make_label("WEEKDAYS ONLY:")
        self.chk_weekdays = QCheckBox("Mon–Fri only")
        self.chk_weekdays.setStyleSheet("color: white; font-size: 16px;")
        self.form_layout.addRow(self.lbl_weekdays, self.chk_weekdays)
        
        # Weight (hidden — payout modes don't use per-chore reward)
        self.spin_weight = QSpinBox()
        self.spin_weight.setRange(1, 10)
        self.spin_weight.setValue(1)
        self.spin_weight.hide()
        
        # --- Rotation-specific fields (hidden by default) ---
        self.lbl_rot_freq = self.make_label("ROTATION TYPE:")
        self.combo_rot_freq = QComboBox()
        self.style_combo(self.combo_rot_freq)
        self.combo_rot_freq.addItems(["ALTERNATING_DAILY", "EVERY_OTHER_DAY", "BIWEEKLY"])
        self.combo_rot_freq.currentIndexChanged.connect(self._update_freq_description)
        self.form_layout.addRow(self.lbl_rot_freq, self.combo_rot_freq)
        self.lbl_rot_freq.hide()
        self.combo_rot_freq.hide()
        
        self.lbl_rot_freq_desc = QLabel("")
        self.lbl_rot_freq_desc.setWordWrap(True)
        self.lbl_rot_freq_desc.setStyleSheet("color: #8899AA; font-size: 14px; padding: 4px 0;")
        self.form_layout.addRow("", self.lbl_rot_freq_desc)
        self.lbl_rot_freq_desc.hide()
        
        self.lbl_rot_members = self.make_label("CREW MEMBERS:")
        self.rotation_member_checks = []
        self.rot_members_widget = QWidget()
        self.rot_members_layout = QVBoxLayout(self.rot_members_widget)
        self.rot_members_layout.setContentsMargins(0, 0, 0, 0)
        self.rot_members_layout.setSpacing(5)
        self.form_layout.addRow(self.lbl_rot_members, self.rot_members_widget)
        self.lbl_rot_members.hide()
        self.rot_members_widget.hide()
        
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
        self.btn_delete.setFixedSize(150, 60)
        self.btn_delete.clicked.connect(self.archive_chore)
        self.btn_delete.hide()
        actions.addWidget(self.btn_delete)
        
        actions.addStretch()
        
        self.btn_save = HoloButton("SAVE QUEST")
        self.btn_save.setFixedSize(250, 60)
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
        
        # Update rotation member checkboxes
        self._rebuild_member_checks()
            
        # 2. Fetch All Chores
        self.list_widget.clear()
        self.chores = []
        
        for k in self.kids:
            kid_chores = ApiService.get_kid_chores(k["id"])
            for c in kid_chores:
                c["kid_name"] = k["name"]
                self.chores.append(c)
                label = f"[{k['name']}] {c['name']}"
                item = QListWidgetItem(label)
                item.setData(Qt.ItemDataRole.UserRole, c)
                self.list_widget.addItem(item)
        
        # 3. Fetch Rotation Groups
        rotations = ApiService.get_rotation_groups()
        for r in rotations:
            member_names = ", ".join(m["kid_name"] for m in r.get("members", []))
            label = f"{r['name']} ({member_names})"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, {"_rotation": True, **r})
            self.list_widget.addItem(item)
    
    def _rebuild_member_checks(self):
        """Rebuild the rotation member checkboxes."""
        # Clear existing
        while self.rot_members_layout.count():
            w = self.rot_members_layout.takeAt(0).widget()
            if w: w.setParent(None)
        self.rotation_member_checks = []
        
        for k in self.kids:
            cb = QCheckBox(k.get("name", "Unknown"))
            cb.setStyleSheet("color: white; font-size: 16px;")
            cb.setProperty("kid_id", k.get("id"))
            self.rotation_member_checks.append(cb)
            self.rot_members_layout.addWidget(cb)
    
    def on_chore_selected(self, item):
        data = item.data(Qt.ItemDataRole.UserRole)
        
        if data.get("_rotation"):
            # Rotation group selected
            self.selected_rotation = data
            self.selected_chore = None
            self.is_rotation_mode = True
            self._show_rotation_fields(True)
            
            self.inp_name.setText(data.get("name", ""))
            self.inp_desc.setText(data.get("description", "") or "")
            
            # Set frequency
            freq = data.get("frequency", "ALTERNATING_DAILY")
            idx = self.combo_rot_freq.findText(freq)
            if idx >= 0: self.combo_rot_freq.setCurrentIndex(idx)
            
            # Check member boxes
            member_ids = [m["kid_id"] for m in data.get("members", [])]
            for cb in self.rotation_member_checks:
                cb.setChecked(cb.property("kid_id") in member_ids)
            
            self.btn_save.setText("UPDATE ROTATION")
            self.btn_delete.show()
            return
        
        # Regular chore selected
        self.selected_chore = data
        self.selected_rotation = None
        self.is_rotation_mode = False
        self._show_rotation_fields(False)
        
        self.inp_name.setText(data.get("name", ""))
        self.inp_desc.setText(data.get("description", "") or "")
        self.spin_weight.setValue(data.get("weight", 1))
        
        freq = data.get("frequency", "DAILY")
        idx = self.combo_freq.findText(freq)
        if idx >= 0: self.combo_freq.setCurrentIndex(idx)
        
        due_day = data.get("due_day")
        if due_day is not None:
            self.combo_day.setCurrentIndex(due_day)
        else:
            self.combo_day.setCurrentIndex(0)
        
        self.chk_weekdays.setChecked(data.get("weekdays_only", False))
        self.on_freq_changed()
        
        target_kid_name = data.get("kid_name")
        for i in range(self.combo_kid.count()):
            if self.combo_kid.itemText(i) == target_kid_name:
                self.combo_kid.setCurrentIndex(i)
                break
                
        self.btn_save.setText("UPDATE QUEST")
        self.btn_delete.show()

    def _update_freq_description(self):
        """Update the frequency description label based on current selection."""
        descs = {
            "ALTERNATING_DAILY": "Due every day — kids take turns. (A today, B tomorrow, A again…)",
            "EVERY_OTHER_DAY": "Due every other day — kids rotate on active days only. Off days = no one does it.",
            "BIWEEKLY": "Due every 2 weeks on the same day of the week as the start date.",
        }
        current = self.combo_rot_freq.currentText()
        self.lbl_rot_freq_desc.setText(descs.get(current, ""))

    def _show_rotation_fields(self, show):
        """Toggle visibility of rotation vs regular chore fields."""
        if show:
            self.combo_kid.hide()
            # Find the label for ASSIGN TO
            for i in range(self.form_layout.rowCount()):
                item = self.form_layout.itemAt(i, QFormLayout.ItemRole.LabelRole)
                if item and item.widget() and "ASSIGN" in item.widget().text():
                    item.widget().hide()
            self.combo_freq.hide()
            for i in range(self.form_layout.rowCount()):
                item = self.form_layout.itemAt(i, QFormLayout.ItemRole.LabelRole)
                if item and item.widget() and "FREQUENCY" in item.widget().text():
                    item.widget().hide()
            self.lbl_day.hide()
            self.combo_day.hide()
            self.lbl_weekdays.hide()
            self.chk_weekdays.hide()
            self.lbl_rot_freq.show()
            self.combo_rot_freq.show()
            self.lbl_rot_freq_desc.show()
            self._update_freq_description()
            self.lbl_rot_members.show()
            self.rot_members_widget.show()
        else:
            self.combo_kid.show()
            for i in range(self.form_layout.rowCount()):
                item = self.form_layout.itemAt(i, QFormLayout.ItemRole.LabelRole)
                if item and item.widget() and "ASSIGN" in item.widget().text():
                    item.widget().show()
            self.combo_freq.show()
            for i in range(self.form_layout.rowCount()):
                item = self.form_layout.itemAt(i, QFormLayout.ItemRole.LabelRole)
                if item and item.widget() and "FREQUENCY" in item.widget().text():
                    item.widget().show()
            self.on_freq_changed()
            self.lbl_rot_freq.hide()
            self.combo_rot_freq.hide()
            self.lbl_rot_freq_desc.hide()
            self.lbl_rot_members.hide()
            self.rot_members_widget.hide()

    def on_add_clicked(self):
        self.list_widget.clearSelection()
        self.selected_chore = None
        self.selected_rotation = None
        self.is_rotation_mode = False
        self._show_rotation_fields(False)
        self.inp_name.clear()
        self.inp_desc.clear()
        self.spin_weight.setValue(1)
        self.combo_freq.setCurrentIndex(0)
        self.combo_day.setCurrentIndex(0)
        self.chk_weekdays.setChecked(False)
        self.on_freq_changed()
        
        self.btn_save.setText("CREATE QUEST")
        self.btn_delete.hide()
        self.inp_name.setFocus()

    def on_add_rotation_clicked(self):
        self.list_widget.clearSelection()
        self.selected_chore = None
        self.selected_rotation = None
        self.is_rotation_mode = True
        self._show_rotation_fields(True)
        self.inp_name.clear()
        self.inp_desc.clear()
        self.combo_rot_freq.setCurrentIndex(0)
        for cb in self.rotation_member_checks:
            cb.setChecked(False)
        
        self.btn_save.setText("CREATE ROTATION")
        self.btn_delete.hide()
        self.inp_name.setFocus()

    def save_chore(self):
        name = self.inp_name.text().strip()
        if not name: return
        
        if self.is_rotation_mode:
            self._save_rotation(name)
            return
        
        desc = self.inp_desc.text().strip()
        weight = self.spin_weight.value()
        freq = self.combo_freq.currentText()
        kid_id = self.combo_kid.currentData()
        
        due_day = None
        weekdays_only = False
        if freq == "WEEKLY":
            due_day = self.combo_day.currentIndex()
        else:
            weekdays_only = self.chk_weekdays.isChecked()
        
        if self.selected_chore:
            cid = self.selected_chore["id"]
            ApiService.update_chore(cid, name=name, description=desc, weight=weight, frequency=freq, due_day=due_day, weekdays_only=weekdays_only)
        else:
            if kid_id is not None:
                ApiService.create_chore(kid_id, name, description=desc, reward=weight, frequency=freq, due_day=due_day, weekdays_only=weekdays_only)
            
        self.refresh_data()
        self.on_add_clicked()

    def _save_rotation(self, name):
        desc = self.inp_desc.text().strip()
        freq = self.combo_rot_freq.currentText()
        
        # Collect checked members
        members = []
        pos = 0
        for cb in self.rotation_member_checks:
            if cb.isChecked():
                members.append({"kid_id": cb.property("kid_id"), "position": pos})
                pos += 1
        
        if len(members) < 1:
            from ..components.holo_alert import HoloAlert
            HoloAlert("VALIDATION ERROR", "Select at least 1 crew member.", self.window(), is_error=True).exec()
            return
        
        if self.selected_rotation:
            # Update — use API directly
            import requests
            requests.put(
                f"http://localhost:8000/api/rotations/{self.selected_rotation['id']}",
                json={"name": name, "description": desc, "frequency": freq, "members": members},
                timeout=2,
            )
        else:
            # Create
            start = date.today().isoformat()
            ApiService.create_rotation_group(name, freq, start, members, description=desc)
        
        self.refresh_data()
        self.on_add_clicked()

    def on_freq_changed(self):
        freq = self.combo_freq.currentText()
        if freq == "WEEKLY":
            self.lbl_day.show()
            self.combo_day.show()
            self.lbl_weekdays.hide()
            self.chk_weekdays.hide()
        else:
            self.lbl_day.hide()
            self.combo_day.hide()
            self.lbl_weekdays.show()
            self.chk_weekdays.show()

    def archive_chore(self):
        if self.selected_rotation:
            ApiService.delete_rotation_group(self.selected_rotation["id"])
            self.refresh_data()
            self.on_add_clicked()
        elif self.selected_chore:
            cid = self.selected_chore["id"]
            ApiService.delete_chore(cid)
            self.refresh_data()
            self.on_add_clicked()
