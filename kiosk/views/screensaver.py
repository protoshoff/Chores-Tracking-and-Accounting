import random
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont

class ScreensaverView(QWidget):
    wake_up = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Screensaver")
        self.setStyleSheet("background-color: black;")
        
        # Floating Label
        self.lbl = QLabel("SYSTEM STANDBY\nTOUCH TO RESUME", self)
        self.lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl.setStyleSheet("color: #00E5FF; font-family: 'Courier New'; font-weight: bold;")
        font = QFont("Courier New", 24)
        font.setBold(True)
        self.lbl.setFont(font)
        self.lbl.adjustSize()
        
        # Animation Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.move_text)
        
        # Velocity
        self.vx = 2
        self.vy = 2

    def showEvent(self, event):
        self.timer.start(50) # 20 FPS
        self.center_text()
        super().showEvent(event)
        
    def hideEvent(self, event):
        self.timer.stop()
        super().hideEvent(event)

    def center_text(self):
        # Start center
        rect = self.rect()
        lb = self.lbl.rect()
        self.lbl.move(
            (rect.width() - lb.width()) // 2,
            (rect.height() - lb.height()) // 2
        )

    def move_text(self):
        # Bounce logic
        pos = self.lbl.pos()
        x, y = pos.x(), pos.y()
        w, h = self.width(), self.height()
        lw, lh = self.lbl.width(), self.lbl.height()
        
        next_x = x + self.vx
        next_y = y + self.vy
        
        if next_x <= 0 or next_x + lw >= w:
            self.vx *= -1
            self.style_color()
            
        if next_y <= 0 or next_y + lh >= h:
            self.vy *= -1
            self.style_color()
            
        self.lbl.move(x + self.vx, y + self.vy)

    def style_color(self):
        # Change color on bounce for fun
        colors = ["#00E5FF", "#FFD700", "#FF0055", "#00FF00"]
        c = random.choice(colors)
        self.lbl.setStyleSheet(f"color: {c}; font-family: 'Courier New'; font-weight: bold;")

    def mousePressEvent(self, event):
        self.wake_up.emit()
