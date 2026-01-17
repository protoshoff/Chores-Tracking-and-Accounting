from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QGridLayout, QFrame
from PySide6.QtCore import Qt, Signal
from ..components.holo_widgets import HoloButton
from ..services.sound import SoundService
from ..services.api import ApiService

class PinPad(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SECURITY CHECK")
        self.setFixedSize(450, 600) # Increased Size
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Main Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4) # Small margin for border
        
        # Container Frame for styling
        self.frame = QFrame()
        self.frame.setObjectName("SecurityPanel")
        # Opaque dark background with border, like a physical device
        self.frame.setStyleSheet("""
            QFrame#SecurityPanel {
                background-color: #050510; 
                border: 2px solid #00E5FF;
                border-radius: 10px;
            }
            QLabel { color: #00E5FF; }
        """)
        
        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setContentsMargins(30, 40, 30, 40) # More internal padding
        
        # -- Title --
        lbl = QLabel("AUTHORIZATION REQUIRED")
        lbl.setStyleSheet("font-size: 18px; font-weight: bold; letter-spacing: 2px; color: #FFD700;") # Slightly smaller font
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame_layout.addWidget(lbl)
        
        # -- Display --
        self.display = QLineEdit()
        self.display.setEchoMode(QLineEdit.EchoMode.Password)
        self.display.setReadOnly(True)
        self.display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.display.setStyleSheet("""
            QLineEdit {
                background-color: black;
                border: 1px solid #333;
                font-size: 32px;
                color: #00E5FF; 
                padding: 10px;
                margin-top: 15px;
            }
        """)
        frame_layout.addWidget(self.display)
        
        frame_layout.addSpacing(30)
        
        # -- Keys --
        keys_grid = QGridLayout()
        
        keys = [
            ('1', 0, 0), ('2', 0, 1), ('3', 0, 2),
            ('4', 1, 0), ('5', 1, 1), ('6', 1, 2),
            ('7', 2, 0), ('8', 2, 1), ('9', 2, 2),
            ('✖', 3, 0), ('0', 3, 1), ('✔', 3, 2),
        ]
        
        for k, r, c in keys:
            btn = QPushButton(k)
            btn.setFixedSize(90, 80) # Faster buttons
            
            if k == '✔':
                 btn.setStyleSheet("background: #003300; border: 1px solid #00FF00; color: #00FF00; font-size: 24px;")
                 btn.clicked.connect(self.verify_pin)
            elif k == '✖':
                 btn.setStyleSheet("background: #330000; border: 1px solid #FF0000; color: #FF0000; font-size: 24px;")
                 btn.clicked.connect(self.clear_pin)
            else:
                 btn.setStyleSheet("""
                    QPushButton {
                        background: #111; 
                        border: 1px solid #007BFF; 
                        color: white; 
                        font-size: 24px;
                    }
                    QPushButton:pressed {
                        background: #007BFF;
                    }
                 """)
                 btn.clicked.connect(lambda _, x=k: self.add_digit(x))
                 
            keys_grid.addWidget(btn, r, c)
            
        frame_layout.addLayout(keys_grid)
        
        # -- Cancel --
        frame_layout.addStretch()
        btn_cancel = QPushButton("CANCEL")
        btn_cancel.setFixedHeight(70) # Taller as requested
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        # High Contrast Red
        btn_cancel.setStyleSheet("background: rgba(255, 0, 85, 0.1); color: #FF0055; font-size: 20px; border: 1px solid #FF0055; border-radius: 4px; margin-top: 20px; font-weight: bold;") 
        btn_cancel.clicked.connect(self.reject)
        frame_layout.addWidget(btn_cancel)
        
        # Add frame to main layout
        layout.addWidget(self.frame)

    # Methods remain the same, just removing the old init code block completely


    def add_digit(self, digit):
        SoundService.play_click()
        if len(self.display.text()) < 4:
            self.display.setText(self.display.text() + digit)

    def clear_pin(self):
        SoundService.play_click()
        self.display.clear()

    def verify_pin(self):
        SoundService.play_click()
        code = self.display.text()
        
        # Verify via API
        if ApiService.verify_pin(code):
            self.accept()
        else:
            SoundService.play_error()
            self.display.clear()
            self.display.setPlaceholderText("INVALID")
