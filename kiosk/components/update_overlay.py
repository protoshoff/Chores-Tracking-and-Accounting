from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

class UpdateOverlay(QDialog):
    """Fullscreen overlay shown during system update"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Dialog
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Make fullscreen
        if parent:
            self.setGeometry(parent.geometry())
        else:
            self.showFullScreen()
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Title with pulsing animation
        self.lbl_title = QLabel("SYSTEM UPDATE IN PROGRESS")
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont("Courier New", 32, QFont.Weight.Bold)
        self.lbl_title.setFont(font)
        self.lbl_title.setStyleSheet("color: #00E5FF; margin-bottom: 40px;")
        layout.addWidget(self.lbl_title)
        
        # Animated dots
        self.lbl_dots = QLabel("...")
        self.lbl_dots.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_dots.setFont(QFont("Courier New", 48, QFont.Weight.Bold))
        self.lbl_dots.setStyleSheet("color: #00E5FF; margin-bottom: 60px;")
        layout.addWidget(self.lbl_dots)
        
        # Status message
        lbl_msg = QLabel(
            "Downloading latest version from GitHub...\n\n"
            "The kiosk will restart automatically.\n"
            "Please do not power off."
        )
        lbl_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_msg.setFont(QFont("Arial", 18))
        lbl_msg.setStyleSheet("color: white; line-height: 1.8;")
        lbl_msg.setWordWrap(True)
        layout.addWidget(lbl_msg)
        
        # Background
        self.setStyleSheet("""
            QDialog {
                background-color: rgba(5, 10, 20, 240);
                border: 3px solid #00E5FF;
            }
        """)
        
        # Animate dots
        self.dot_count = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate_dots)
        self.timer.start(500)  # Update every 500ms
    
    def animate_dots(self):
        """Animate the dots to show activity"""
        self.dot_count = (self.dot_count + 1) % 4
        self.lbl_dots.setText("." * (self.dot_count + 1))
