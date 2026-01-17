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
        self.lbl = QLabel("SYSTEM STANDBY\n<span style='font-size: 30px;'>TOUCH TO RESUME</span>", self)
        self.lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Use simple CSS for everything to avoid QFont/QSS conflicts
        self.lbl.setStyleSheet("""
            color: #00E5FF; 
            font-family: 'Orbitron'; 
            font-weight: bold; 
            font-size: 60px;
            border: 2px solid #00E5FF;
            padding: 40px;
            background-color: rgba(0, 20, 40, 220);
            border-radius: 15px;
        """)
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
        
        # Check X collisions
        if next_x <= 0:
            self.vx = abs(self.vx) # Force positive
            next_x = 0
            self.style_color()
        elif next_x + lw >= w:
            self.vx = -abs(self.vx) # Force negative
            next_x = w - lw
            self.style_color()
            
        # Check Y collisions
        if next_y <= 0:
            self.vy = abs(self.vy) # Force positive
            next_y = 0
            self.style_color()
        elif next_y + lh >= h:
            self.vy = -abs(self.vy) # Force negative
            next_y = h - lh
            self.style_color()
            
        self.lbl.move(next_x, next_y)

    def style_color(self):
        # Change color on bounce for fun
        colors = ["#00E5FF", "#FFD700", "#FF0055", "#00FF00"]
        c = random.choice(colors)
        
        # Only update colors, don't resize or change text content dynamically
        # changing text content causes resize which causes bugs
        
        # Update stylesheet but keep font sizes fixed as defined in init/style
        self.lbl.setStyleSheet(f"""
            color: {c}; 
            font-family: 'Orbitron'; 
            font-weight: bold; 
            font-size: 60px;
            border: 2px solid {c};
            padding: 40px;
            background-color: rgba(0, 20, 40, 220);
            border-radius: 15px;
        """)
        
        # Re-set text to ensure the span color matches if we want, or just let CSS handle main color.
        # The span color override in previous code might be fighting.
        # Let's simplify: Inherit color for the span unless we explicitly want it different.
        # Actually, simpler: Just set the main widget color. The span will inherit if we remove 'color:{c}' from span style.
        
        self.lbl.setText(f"SYSTEM STANDBY\n<span style='font-size: 30px;'>TOUCH TO RESUME</span>")
        # self.lbl.adjustSize() <-- REMOVED to prevent jitter

    def mousePressEvent(self, event):
        self.wake_up.emit()
