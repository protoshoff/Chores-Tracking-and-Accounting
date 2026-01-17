from PySide6.QtWidgets import QWidget, QFrame, QPushButton, QGraphicsDropShadowEffect, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QRectF, QPointF, QSize
from PySide6.QtGui import QPainter, QPen, QColor, QPainterPath, QBrush, QFont, QPalette
from ..services.sound import SoundService

class HoloButton(QPushButton):
    def __init__(self, text, parent=None, is_primary=True):
        super().__init__(text, parent)
        self.is_primary = is_primary
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(50)
        self.setMinimumWidth(120)
        
        # Glow Effect - Subtle Depth instead of Neon
        self._glow = QGraphicsDropShadowEffect(self)
        self._glow.setBlurRadius(10)
        self._glow.setColor(QColor(0, 0, 0, 100)) # Black shadow
        self._glow.setOffset(2, 2)
        self.setGraphicsEffect(self._glow)

    def mousePressEvent(self, e):
        SoundService.play_click()
        super().mousePressEvent(e)
        
    # def paintEvent(self, event):
    #     # DISABLED for Modern Admin Theme alignment via QSS
    #     pass


class HoloFrame(QFrame):
    def __init__(self, title="PANEL", parent=None):
        super().__init__(parent)
        self.setObjectName("HoloBox")
        self.title = title
        self.setStyleSheet("background: transparent;")
        
        # Glow (Match Web Admin box-shadow: 0 0 30px rgba(0, 229, 255, 0.2))
        self._glow = QGraphicsDropShadowEffect(self)
        self._glow.setBlurRadius(30)
        self._glow.setColor(QColor(0, 229, 255, 50)) # ~0.2 alpha
        self._glow.setOffset(0,0)
        self.setGraphicsEffect(self._glow)

    # def paintEvent(self, event):
    #     # DISABLED for Modern Admin Theme alignment via QSS
    #     pass
