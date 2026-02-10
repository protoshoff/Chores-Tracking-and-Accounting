from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QScrollArea, QFrame, QLineEdit, QDialog, QMessageBox)
from PySide6.QtCore import Qt, Signal, QTimer, QThread
from ..components.holo_widgets import HoloButton, HoloFrame
import requests

# Worker Thread for connecting (as it might take 10s)
class ConnectThread(QThread):
    finished = Signal(bool, str) # success, message
    
    def __init__(self, ssid, pwd):
        super().__init__()
        self.ssid = ssid
        self.pwd = pwd
        
    def run(self):
        try:
            resp = requests.post("http://localhost:8000/api/system/wifi/connect", 
                                 json={"ssid": self.ssid, "password": self.pwd})
            if resp.status_code == 200:
                self.finished.emit(True, self.ssid)
            else:
                self.finished.emit(False, "Connection Failed")
        except Exception as e:
            self.finished.emit(False, str(e))

class SimpleKeyboard(QDialog):
    """ On-screen keyboard with Shift and Special Characters support. """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Enter Password")
        self.setFixedSize(750, 450)  # Increased width to prevent backspace clipping
        self.setStyleSheet("background-color: #0A0A12; color: #E0E0E0;")
        
        layout = QVBoxLayout(self)
        self.display = QLineEdit()
        self.display.setEchoMode(QLineEdit.EchoMode.Password)
        self.display.setStyleSheet("font-size: 24px; padding: 10px; border: 1px solid #00F; background: #000; color: #FFF;")
        layout.addWidget(self.display)
        
        self.is_shifted = False
        self.is_symbols = False
        
        # Container for keys to allow refreshing layout
        self.keys_widget = QWidget()
        self.keys_layout = QVBoxLayout(self.keys_widget)
        layout.addWidget(self.keys_widget)
        
        self.render_keys()
        
    def render_keys(self):
        # Clear existing keys - PROPERLY clear both widgets and layouts
        while self.keys_layout.count():
            child = self.keys_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                # Recursively clear and delete nested layout
                self._clear_layout(child.layout())

        # Define Layouts
        # Normal (Lower)
        chars_lower = [
            "1234567890",
            "qwertyuiop",
            "asdfghjkl",
            "zxcvbnm"
        ]
        
        # Shifted (Upper)
        chars_upper = [
            "!@#$%^&*()",
            "QWERTYUIOP",
            "ASDFGHJKL",
            "ZXCVBNM"
        ]
        
        # Symbols
        chars_sym = [
            "1234567890",
            "-/:;()$&@\"",
            ".,?!'[]{}",
            "~<>\\|^=+_%" 
        ]

        if self.is_symbols:
            current_rows = chars_sym
        elif self.is_shifted:
            current_rows = chars_upper
        else:
            current_rows = chars_lower

        # Render rows
        for i, row_str in enumerate(current_rows):
            row_layout = QHBoxLayout()
            for char in row_str:
                btn = QPushButton(char)
                btn.setFixedSize(60, 50)
                btn.setStyleSheet("background: #222; border: 1px solid #555; font-size: 20px; border-radius: 4px; text-transform: none;")
                btn.clicked.connect(lambda _, c=char: self.display.setText(self.display.text() + c))
                row_layout.addWidget(btn)
            
            # Add Backspace to first row
            if i == 0:
                btn_bs = QPushButton("⌫")
                btn_bs.setFixedSize(75, 50)  # Reduced to 75px with wider keyboard
                btn_bs.setStyleSheet("background: #442222; border: 1px solid #F55; font-size: 18px;")
                btn_bs.clicked.connect(self.backspace)
                row_layout.addWidget(btn_bs)

            self.keys_layout.addLayout(row_layout)

        # Control Row (Shift, Space, Sym, Enter)
        ctrl_layout = QHBoxLayout()
        
        # Shift
        lbl_shift = "⇧ SHIFT" if not self.is_shifted else "⬆ SHIFT"
        style_shift = "background: #222;" if not self.is_shifted else "background: #004488; color: white;"
        btn_shift = QPushButton(lbl_shift)
        btn_shift.setFixedSize(120, 50)  # Increased to 120 to prevent clipping
        btn_shift.setStyleSheet(style_shift + " border: 1px solid #555;")
        btn_shift.clicked.connect(self.toggle_shift)
        ctrl_layout.addWidget(btn_shift)

        # Symbols
        lbl_sym = "?123" if not self.is_symbols else "ABC"
        btn_sym = QPushButton(lbl_sym)
        btn_sym.setFixedSize(90, 50)  # Increased to 90 to prevent clipping
        btn_sym.setStyleSheet("background: #222; border: 1px solid #555;")
        btn_sym.clicked.connect(self.toggle_symbols)
        ctrl_layout.addWidget(btn_sym)

        # Space
        btn_space = QPushButton("SPACE")
        btn_space.setFixedHeight(50) 
        btn_space.setStyleSheet("background: #333; border: 1px solid #666;")
        btn_space.clicked.connect(lambda: self.display.setText(self.display.text() + " "))
        ctrl_layout.addWidget(btn_space)

        # OK / Cancel
        btn_cancel = QPushButton("CANCEL")
        btn_cancel.setFixedSize(130, 50)  # FIX: Was 90→120, now 130 for full text
        btn_cancel.setStyleSheet("background: #552222; color: white;")
        btn_cancel.clicked.connect(self.reject)
        ctrl_layout.addWidget(btn_cancel)

        btn_ok = QPushButton("CONNECT")
        btn_ok.setFixedSize(140, 50)  # FIX: Was 110, increased to 140
        btn_ok.setStyleSheet("background: #007BFF; color: white; font-weight: bold;")
        btn_ok.clicked.connect(self.accept)
        ctrl_layout.addWidget(btn_ok)
        
        self.keys_layout.addLayout(ctrl_layout)
    
    def _clear_layout(self, layout):
        """Recursively clear a layout and all its children."""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self._clear_layout(child.layout())

    def toggle_shift(self):
        self.is_shifted = not self.is_shifted
        self.render_keys()

    def toggle_symbols(self):
        self.is_symbols = not self.is_symbols
        self.is_shifted = False # Reset shift when switching modes
        self.render_keys()

    def backspace(self):
        text = self.display.text()
        self.display.setText(text[:-1])

    def get_text(self):
        return self.display.text()

class AdminWifiView(QWidget):
    back_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        
        main = QVBoxLayout(self)
        
        # Header
        top = QHBoxLayout()
        btn_back = HoloButton("← Back", is_primary=False)
        btn_back.setFixedSize(120, 50)
        btn_back.clicked.connect(self.back_clicked.emit)
        top.addWidget(btn_back)
        
        lbl_title = QLabel("WIFI CONFIGURATOR")
        lbl_title.setObjectName("HoloHeader")
        top.addWidget(lbl_title)
        
        top.addStretch()
        
        btn_scan = HoloButton("↻ Scan", is_primary=False)
        btn_scan.setFixedSize(120, 50)
        btn_scan.clicked.connect(self.scan_networks)
        top.addWidget(btn_scan)
        
        main.addLayout(top)
        
        # Status
        self.lbl_status = QLabel("Checking status...")
        self.lbl_status.setStyleSheet("font-size: 18px; color: #AAA; padding: 10px; font-weight: bold;")
        main.addWidget(self.lbl_status)
        
        # List Container
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        # Transparent scroll background
        scroll.setStyleSheet("background: transparent; border: none;")
        
        self.container_widget = QWidget()
        self.container_widget.setStyleSheet("background: transparent;")
        self.list_layout = QVBoxLayout(self.container_widget)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self.container_widget)
        main.addWidget(scroll)
        
        # Initial Scan
        QTimer.singleShot(500, self.refresh_status)
        QTimer.singleShot(1000, self.scan_networks)

    def refresh_status(self):
        try:
            resp = requests.get("http://localhost:8000/api/system/status")
            if resp.status_code == 200:
                data = resp.json()
                wifi = data.get("wifi", {})
                if wifi.get("connected"):
                    self.lbl_status.setText(f"CONNECTED TO: {wifi['ssid']} ({wifi['ip']})")
                    self.lbl_status.setStyleSheet("color: #00E5FF; font-size: 18px; font-weight: bold;")
                else:
                    self.lbl_status.setText("❌ DISCONNECTED")
                    self.lbl_status.setStyleSheet("color: #FF5555; font-size: 18px; font-weight: bold;")
        except:
            self.lbl_status.setText("⚠ API Offline")

    def scan_networks(self):
        # Clear list
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget(): item.widget().setParent(None)
            
        self.list_layout.addWidget(QLabel("SCANNING..."))
        
        try:
            resp = requests.get("http://localhost:8000/api/system/wifi/scan")
            # Remove "Scanning..."
            if self.list_layout.count() > 0:
                self.list_layout.takeAt(0).widget().setParent(None)
            
            if resp.status_code == 200:
                networks = resp.json()
                if not networks:
                     self.list_layout.addWidget(QLabel("NO NETWORKS FOUND"))
                
                for net in networks:
                    row = self._create_row(net)
                    self.list_layout.addWidget(row)
            else:
                 self.list_layout.addWidget(QLabel("SCAN FAILED"))
        except:
             self.list_layout.addWidget(QLabel("NETWORK ERROR"))

    def _create_row(self, net):
        # Sci-Fi Row
        frame = QFrame()
        # Dark transparent blue bg with cyan border
        frame.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 123, 255, 0.1); 
                border: 1px solid #007BFF; 
                border-radius: 4px; 
                margin-bottom: 5px;
            }
        """)
        layout = QHBoxLayout(frame)
        
        info = QLabel(f"{net['ssid']} ({net['signal']}%)")
        info.setStyleSheet("font-size: 20px; font-weight: bold; color: white; border: none; background: transparent;")
        layout.addWidget(info)
        
        layout.addStretch()
        
        btn_connect = HoloButton("CONNECT")
        btn_connect.setFixedSize(140, 50)
        btn_connect.clicked.connect(lambda: self.prompt_connect(net['ssid']))
        layout.addWidget(btn_connect)
        
        return frame

    def prompt_connect(self, ssid):
        dlg = SimpleKeyboard(self)
        dlg.setWindowTitle(f"Password for {ssid}")
        if dlg.exec():
            pwd = dlg.get_text()
            self.start_connection(ssid, pwd)

    def start_connection(self, ssid, pwd):
        self.lbl_status.setText(f"CONNECTING TO {ssid}...")
        self.lbl_status.setStyleSheet("color: #FFD700;")
        
        self.worker = ConnectThread(ssid, pwd)
        self.worker.finished.connect(self.on_connect_finished)
        self.worker.start()

    def on_connect_finished(self, success, msg):
        if success:
            QMessageBox.information(self, "Success", f"Connected to {msg}")
            self.refresh_status()
        else:
            QMessageBox.warning(self, "Failed", f"Could not connect: {msg}")
            self.refresh_status()
