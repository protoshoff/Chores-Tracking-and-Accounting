from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QComboBox, QSpinBox, QFormLayout)
from PySide6.QtCore import Signal, Qt
from ..components.holo_widgets import HoloButton, HoloFrame
from ..components.holo_alert import HoloAlert
from ..services.api import ApiService

class SettingsView(QWidget):
    back_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_config = {}
        
        main = QVBoxLayout(self)
        
        # Header
        top = QHBoxLayout()
        btn_back = HoloButton("← BACK", is_primary=False)
        btn_back.setFixedSize(120, 50)
        btn_back.clicked.connect(self.back_clicked.emit)
        top.addWidget(btn_back)
        
        lbl_title = QLabel("SYSTEM SETTINGS")
        lbl_title.setObjectName("HoloHeader")
        top.addWidget(lbl_title)
        top.addStretch()
        main.addLayout(top)
        
        # Content Frame
        content_frame = HoloFrame("PAYOUT CONFIGURATION")
        cf_layout = QVBoxLayout(content_frame)
        cf_layout.setContentsMargins(40, 100, 40, 40)
        
        # Form
        form = QFormLayout()
        form.setSpacing(30)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        # Payout Mode Dropdown
        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["All-or-Nothing", "Proportional"])
        self.combo_mode.setStyleSheet("""
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
        self.combo_mode.currentIndexChanged.connect(self.on_mode_changed)
        
        lbl_mode = QLabel("PAYOUT MODE:")
        lbl_mode.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        form.addRow(lbl_mode, self.combo_mode)
        
        # Mode description
        self.lbl_mode_desc = QLabel()
        self.lbl_mode_desc.setWordWrap(True)
        self.lbl_mode_desc.setStyleSheet("color: #888; font-size: 14px; margin-left: 20px;")
        form.addRow("", self.lbl_mode_desc)
        
        # Threshold Spinner
        self.spin_threshold = QSpinBox()
        self.spin_threshold.setRange(0, 100)
        self.spin_threshold.setSuffix("%")
        self.spin_threshold.setValue(80)
        self.spin_threshold.setFixedWidth(120)
        self.spin_threshold.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spin_threshold.setStyleSheet("""
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
        
        self.lbl_threshold = QLabel("PAYOUT THRESHOLD:")
        self.lbl_threshold.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        form.addRow(self.lbl_threshold, self.spin_threshold)
        
        # Threshold description
        self.lbl_threshold_desc = QLabel(
            "Percentage of chores required to earn FULL allowance.\n"
            "Below this threshold, allowance is $0."
        )
        self.lbl_threshold_desc.setWordWrap(True)
        self.lbl_threshold_desc.setStyleSheet("color: #888; font-size: 14px; margin-left: 20px;")
        form.addRow("", self.lbl_threshold_desc)
        
        cf_layout.addLayout(form)
        cf_layout.addStretch()
        
        # Action Buttons
        actions = QHBoxLayout()
        actions.addStretch()
        
        btn_cancel = HoloButton("CANCEL", is_primary=False)
        btn_cancel.setFixedSize(150, 60)
        btn_cancel.clicked.connect(self.back_clicked.emit)
        actions.addWidget(btn_cancel)
        
        btn_save = HoloButton("SAVE SETTINGS")
        btn_save.setFixedSize(220, 60)
        btn_save.clicked.connect(self.save_settings)
        actions.addWidget(btn_save)
        
        cf_layout.addLayout(actions)
        
        main.addWidget(content_frame)
        
        
    def showEvent(self, event):
        self.load_settings()
        super().showEvent(event)
        
    def load_settings(self):
        """Load current settings from API"""
        config = ApiService.get_system_config()
        if config:
            self.current_config = config
            
            # Set mode
            payout_mode = config.get("payout_mode", "ALL_OR_NOTHING")
            if payout_mode == "PRORATED":
                self.combo_mode.setCurrentIndex(1)
            else:
                self.combo_mode.setCurrentIndex(0)
            
            # Set threshold
            threshold = config.get("payout_threshold", 80)
            self.spin_threshold.setValue(threshold)
            
            # Update UI visibility
            self.on_mode_changed()
            
    def on_mode_changed(self):
        """Update UI based on selected payout mode"""
        mode_index = self.combo_mode.currentIndex()
        
        if mode_index == 0:  # All-or-Nothing
            self.lbl_mode_desc.setText(
                "✓ Full allowance if threshold is met\n"
                "✗ Zero allowance if below threshold"
            )
            self.lbl_threshold.setVisible(True)
            self.spin_threshold.setVisible(True)
            self.lbl_threshold_desc.setVisible(True)
        else:  # Proportional
            self.lbl_mode_desc.setText(
                "✓ Allowance proportional to completed chores\n"
                "✓ 50% chores = 50% allowance"
            )
            self.lbl_threshold.setVisible(False)
            self.spin_threshold.setVisible(False)
            self.lbl_threshold_desc.setVisible(False)
            
    def save_settings(self):
        """Save settings to API"""
        mode_index = self.combo_mode.currentIndex()
        payout_mode = "PRORATED" if mode_index == 1 else "ALL_OR_NOTHING"
        threshold = self.spin_threshold.value()
        
        success = ApiService.update_system_config(payout_mode, threshold)
        
        if success:
            HoloAlert("SUCCESS", "System settings updated successfully.", self.window()).exec()
            self.back_clicked.emit()
        else:
            HoloAlert("ERROR", "Failed to update settings. Check backend logs.", 
                     self.window(), is_error=True).exec()
