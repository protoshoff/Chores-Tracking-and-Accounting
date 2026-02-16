from PySide6.QtWidgets import QDialog, QVBoxLayout, QGridLayout, QLabel, QLineEdit
from PySide6.QtCore import Qt, Signal
from .holo_widgets import HoloButton

class HoloKeyboard(QDialog):
    def __init__(self, parent=None, initial_text="", title="KEYPAD"):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(800, 500) # Slightly taller for title
        
        self.result_text = initial_text
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        if title:
             lbl_title = QLabel(title)
             lbl_title.setStyleSheet("font-size: 20px; color: #FFD700; font-weight: bold; margin-bottom: 5px;")
             lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
             layout.addWidget(lbl_title)
        
        # Display Area
        self.display = QLabel(initial_text)
        self.display.setObjectName("HoloHeader")
        self.display.setStyleSheet("background-color: rgba(0, 20, 40, 200); border: 2px solid #00F0FF; padding: 10px; font-size: 32px;")
        layout.addWidget(self.display)
        
        # Keyboard Grid
        grid = QGridLayout()
        grid.setSpacing(5)
        
        self.alpha_keys = [
            ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'],
            ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
            ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
            ['Z', 'X', 'C', 'V', 'B', 'N', 'M']
        ]
        
        self.symbol_keys = [
            ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')'],
            ['-', '_', '=', '+', '[', ']', '{', '}', '|', '\\'],
            [';', ':', "'", '"', ',', '.', '/', '?'],
            ['<', '>', '~', '`']
        ]
        
        self.grid = grid
        self.showing_symbols = False
        self._render_keys(self.alpha_keys)
            
        layout.addLayout(grid)
        
        # Bottom Row
        bottom = QGridLayout()
        
        self._btn_sym = HoloButton("!@#", is_primary=False)
        self._btn_sym.setMinimumWidth(70)
        self._btn_sym.clicked.connect(self._toggle_symbols)
        bottom.addWidget(self._btn_sym, 0, 0)
        
        btn_clear = HoloButton("CLR", is_primary=False)
        btn_clear.setMinimumWidth(70)
        btn_clear.clicked.connect(self.clear)
        bottom.addWidget(btn_clear, 0, 1)
        
        btn_space = HoloButton("SPACE")
        btn_space.setMinimumWidth(160)
        btn_space.clicked.connect(lambda: self.on_key(" "))
        bottom.addWidget(btn_space, 0, 2, 1, 3)
        
        btn_backspace = HoloButton("⌫")
        btn_backspace.setMinimumWidth(90)
        btn_backspace.clicked.connect(self.backspace)
        bottom.addWidget(btn_backspace, 0, 5, 1, 2)
        
        btn_cancel = HoloButton("CANCEL", is_primary=False)
        btn_cancel.setMinimumWidth(100)
        btn_cancel.clicked.connect(self.reject)
        bottom.addWidget(btn_cancel, 0, 7)
        
        btn_enter = HoloButton("ENTER")
        btn_enter.setMinimumWidth(100)
        btn_enter.clicked.connect(self.accept)
        bottom.addWidget(btn_enter, 0, 8)
        
        layout.addLayout(bottom)
        
        # Styling
        self.setStyleSheet("""
            QDialog {
                background-color: rgba(5, 10, 20, 240);
                border: 2px solid #00F0FF;
            }
        """)

    def _render_keys(self, keys):
        """Render a key layout into the grid, clearing existing keys first."""
        # Remove existing key buttons from grid
        for i in reversed(range(self.grid.count())):
            item = self.grid.itemAt(i)
            if item and item.widget():
                item.widget().setParent(None)
        
        for r, row in enumerate(keys):
            for c, key in enumerate(row):
                self.add_key(self.grid, key, r, c)
    
    def _toggle_symbols(self):
        self.showing_symbols = not self.showing_symbols
        if self.showing_symbols:
            self._render_keys(self.symbol_keys)
            self._btn_sym.setText("ABC")
        else:
            self._render_keys(self.alpha_keys)
            self._btn_sym.setText("!@#")

    def add_key(self, grid, char, r, c):
        btn = HoloButton(char)
        btn.setFixedSize(70, 60)  # Slightly wider for better text fit
        btn.clicked.connect(lambda: self.on_key(char))
        grid.addWidget(btn, r, c)

    def on_key(self, char):
        self.result_text += char
        self.display.setText(self.result_text)
        
    def backspace(self):
        self.result_text = self.result_text[:-1]
        self.display.setText(self.result_text)

    def clear(self):
        self.result_text = ""
        self.display.setText("")
        
    def get_text(self):
        return self.result_text

# Helper Wrapper
class HoloLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True) # Force touch interaction
        self.setStyleSheet("""
            QLineEdit {
                background-color: rgba(0, 20, 40, 150);
                border: 1px solid #00F0FF;
                color: #00F0FF;
                padding: 10px;
                font-family: 'Orbitron';
                font-size: 18px;
            }
        """)

    def mousePressEvent(self, event):
        # Open Keyboard
        dlg = HoloKeyboard(self.window(), self.text())
        # Center on screen
        rect = self.window().geometry()
        dlg.move(
            rect.center().x() - dlg.width() // 2,
            rect.center().y() - dlg.height() // 2
        )
        if dlg.exec():
            self.setText(dlg.get_text())
            self.editingFinished.emit() 
        # Don't call super to prevent cursor placement/focus issues
