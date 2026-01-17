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
    """ Crude on-screen keyboard for password entry. Staying basic for now but dark mode. """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Enter Password")
        self.setFixedSize(600, 400)
        self.setStyleSheet("background-color: #0A0A12; color: #E0E0E0;")
        
        layout = QVBoxLayout(self)
        self.display = QLineEdit()
        self.display.setEchoMode(QLineEdit.EchoMode.Password)
        self.display.setStyleSheet("font-size: 24px; padding: 10px; border: 1px solid #00F; background: #000; color: #FFF;")
        layout.addWidget(self.display)
        
        # Keys
        rows = [
            "1234567890",
            "qwertyuiop",
            "asdfghjkl",
            "zxcvbnm"
        ]
        
        for row_str in rows:
            row_layout = QHBoxLayout()
            for char in row_str:
                btn = QPushButton(char)
                btn.setFixedSize(50, 50)
                btn.setStyleSheet("background: #222; border: 1px solid #555; font-size: 18px;")
                btn.clicked.connect(lambda _, c=char: self.display.setText(self.display.text() + c))
                row_layout.addWidget(btn)
            layout.addLayout(row_layout)
            
        # Controls
        ctrl_layout = QHBoxLayout()
        btn_clear = QPushButton("CLR")
        btn_clear.clicked.connect(self.display.clear)
        ctrl_layout.addWidget(btn_clear)
        
        btn_space = QPushButton("SPACE")
        btn_space.clicked.connect(lambda: self.display.setText(self.display.text() + " "))
        ctrl_layout.addWidget(btn_space)
        
        btn_ok = QPushButton("OK")
        btn_ok.setStyleSheet("background-color: #007BFF; color: white;")
        btn_ok.clicked.connect(self.accept)
        ctrl_layout.addWidget(btn_ok)
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        ctrl_layout.addWidget(btn_cancel)
        
        layout.addLayout(ctrl_layout)
        
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
                    self.lbl_status.setText(f"✅ CONNECTED TO: {wifi['ssid']} ({wifi['ip']})")
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
        btn_connect.setFixedSize(120, 40)
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
