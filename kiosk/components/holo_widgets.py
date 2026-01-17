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
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        w = rect.width()
        h = rect.height()
        
        # Chamfer amount
        c = 10 
        
        # Create Path (Chamfered Rect)
        path = QPainterPath()
        path.moveTo(c, 0)
        path.lineTo(w - c, 0)
        path.lineTo(w, c)
        path.lineTo(w, h - c)
        path.lineTo(w - c, h)
        path.lineTo(c, h)
        path.lineTo(0, h - c)
        path.lineTo(0, c)
        path.closeSubpath()
        
        # Colors
        base_color = QColor(0, 229, 255) if self.is_primary else QColor(255, 255, 255)
        if not self.isEnabled():
            base_color = QColor(100, 100, 100)
            
        # Hover/Press Logic
        if self.isDown():
            fill_color = base_color.darker(150)
            fill_alpha = 100
        elif self.underMouse():
            fill_color = base_color
            fill_alpha = 50
        else:
            fill_color = QColor(0, 0, 0)
            fill_alpha = 100 # Semi-transparent dark
            
        # Draw Fill
        painter.setBrush(QBrush(QColor(0, 0, 0, 150))) # Dark BG always
        painter.drawPath(path)
        
        if self.underMouse() or self.isDown():
             painter.setBrush(QBrush(QColor(base_color.red(), base_color.green(), base_color.blue(), 50)))
             painter.drawPath(path)
             
        # Draw Border
        pen = QPen(base_color)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)
        
        # Draw Text
        painter.setPen(QColor("#FFFFFF"))
        font = self.font()
        font.setBold(True)
        # font.setFamily("Orbitron") # If available
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.text())


class HoloFrame(QFrame):
    def __init__(self, title="PANEL", parent=None):
        super().__init__(parent)
        self.title = title
        self.setStyleSheet("background: transparent;")
        
        # Glow (Match Web Admin box-shadow: 0 0 30px rgba(0, 229, 255, 0.2))
        self._glow = QGraphicsDropShadowEffect(self)
        self._glow.setBlurRadius(30)
        self._glow.setColor(QColor(0, 229, 255, 50)) # ~0.2 alpha
        self._glow.setOffset(0,0)
        self.setGraphicsEffect(self._glow)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        w = rect.width()
        h = rect.height()
        
        # Margins for glow
        m = 10
        inner_rect = rect.adjusted(m, m, -m, -m)
        iw = inner_rect.width()
        ih = inner_rect.height()
        x = inner_rect.x()
        y = inner_rect.y()
        
        # Chamfer
        c = 20
        
        path = QPainterPath()
        path.moveTo(x + c, y)
        path.lineTo(x + iw - c, y)
        path.lineTo(x + iw, y + c)
        path.lineTo(x + iw, y + ih - c)
        path.lineTo(x + iw - c, y + ih)
        path.lineTo(x + c, y + ih)
        path.lineTo(x, y + ih - c)
        path.lineTo(x, y + c)
        path.closeSubpath()
        
        # Fill (Match Web Admin --panel-bg: rgba(0, 20, 40, 0.8))
        painter.setBrush(QBrush(QColor(0, 20, 40, 205))) 
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPath(path)
        
        # Border (Match Web Admin: 1px solid rgba(0, 229, 255, 0.3))
        pen = QPen(QColor(0, 229, 255, 76)) 
        pen.setWidth(1)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)
        
        # Title Bar Decoration
        # Draw a line below title area
        title_h = 60
        painter.setPen(QPen(QColor("#007BFF"), 1))
        painter.drawLine(x + c, y + title_h, x + iw - c, y + title_h)
        
        # Draw Title Text
        painter.setPen(QColor("#00E5FF"))
        font = self.font()
        font.setPointSize(24)
        font.setBold(True)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2)
        painter.setFont(font)
        
        title_rect = QRectF(x, y, iw, title_h)
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignCenter, self.title)
