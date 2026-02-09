from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from .holo_widgets import HoloButton

class HoloAlert(QDialog):
    def __init__(self, title="ALERT", message="", parent=None, is_error=False, show_cancel=False):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(500, 300)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Title
        lbl_title = QLabel(title)
        lbl_title.setObjectName("HoloHeader")
        color = "#FF0000" if is_error else "#00E5FF"
        lbl_title.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color};")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_title)
        
        # Message
        lbl_msg = QLabel(message)
        lbl_msg.setWordWrap(True)
        lbl_msg.setStyleSheet("font-size: 18px; color: white;")
        lbl_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_msg)
        
        layout.addStretch()
        
        # Buttons
        if show_cancel:
            # Show both OK and CANCEL buttons
            from PySide6.QtWidgets import QHBoxLayout
            btn_layout = QHBoxLayout()
            
            btn_cancel = HoloButton("CANCEL", is_primary=False)
            btn_cancel.clicked.connect(self.reject)
            btn_layout.addWidget(btn_cancel)
            
            btn_ok = HoloButton("OK")
            btn_ok.clicked.connect(self.accept)
            btn_layout.addWidget(btn_ok)
            
            layout.addLayout(btn_layout)
        else:
            # Single ACKNOWLEDGE button
            self.btn_ok = HoloButton("ACKNOWLEDGE")
            self.btn_ok.clicked.connect(self.accept)
            layout.addWidget(self.btn_ok)
        
        # Styling
        border = "#FF0000" if is_error else "#00F0FF"
        self.setStyleSheet(f"""
            QDialog {{
                background-color: rgba(5, 10, 20, 250);
                border: 2px solid {border};
                border-radius: 10px;
            }}
        """)
