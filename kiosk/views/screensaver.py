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
        # Use HTML for multi-size text
        self.lbl = QLabel("SYSTEM STANDBY\n<span style='font-size: 30px;'>TOUCH TO RESUME</span>", self)
        self.lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl.setFixedSize(600, 250) # Fixed size to prevent jitter
        
        # Initial Style
        self.update_style("#00E5FF")
        
        # Animation Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.move_text)
        
        # Velocity
        self.vx = 2
        self.vy = 2

    def showEvent(self, event):
        self.timer.start(20) # 50 FPS for smoothness
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
        
        collision = False
        
        # Check X collisions
        if next_x <= 0:
            self.vx = abs(self.vx)
            next_x = 0
            collision = True
        elif next_x + lw >= w:
            self.vx = -abs(self.vx)
            next_x = w - lw
            collision = True
            
        # Check Y collisions
        if next_y <= 0:
            self.vy = abs(self.vy)
            next_y = 0
            collision = True
        elif next_y + lh >= h:
            self.vy = -abs(self.vy)
            next_y = h - lh
            collision = True
            
        self.lbl.move(next_x, next_y)
        
        if collision:
            self.randomize_color()

    def randomize_color(self):
        colors = ["#00E5FF", "#FFD700", "#FF0055", "#00FF00"]
        c = random.choice(colors)
        self.update_style(c)
        
    def update_style(self, color):
        # Only update CSS, do NOT touch text content
        self.lbl.setStyleSheet(f"""
            color: {color}; 
            font-family: 'Orbitron'; 
            font-weight: bold; 
            font-size: 60px;
            border: 2px solid {color};
            padding: 40px;
            background-color: rgba(0, 20, 40, 220);
            border-radius: 15px;
        """)
        # We rely on the initial setText being sufficient. 
        # The color of the <span> in HTML won't update automatically via CSS 'color' unless it inherits?
        # Actually standard HTML spans inherit color if not specified.
        # In my initial setText I removed the color spec from span, so it should inherit correctly from the parent stylesheet.

    def mousePressEvent(self, event):
        self.wake_up.emit()
