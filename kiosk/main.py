import sys
import os
import subprocess
print("DEBUG: Python Script Starting...")

def detect_screen_resolution():
    """Detect screen resolution before Qt starts using xrandr."""
    try:
        result = subprocess.run(['xrandr'], capture_output=True, text=True, timeout=2)
        for line in result.stdout.split('\n'):
            if ' connected' in line and 'primary' in line:
                # Extract resolution from lines like: "HDMI-1 connected primary 1920x1200+0+0"
                parts = line.split()
                for part in parts:
                    if 'x' in part and '+' in part:
                        resolution = part.split('+')[0]
                        width, height = map(int, resolution.split('x'))
                        print(f"DEBUG: Detected screen resolution via xrandr: {width}x{height}")
                        return width, height
        print("DEBUG: Could not parse xrandr output, will use Qt detection as fallback")
        return None, None
    except Exception as e:
        print(f"DEBUG: xrandr detection failed ({e}), will use Qt detection as fallback")
        return None, None

# Detect and set DPI scaling BEFORE importing Qt
screen_width, screen_height = detect_screen_resolution()
if screen_width and screen_width >= 1920:
    scale_factor = round(screen_width / 1024.0, 2)
    print(f"DEBUG: High-res display detected. Setting QT_SCALE_FACTOR={scale_factor}")
    os.environ["QT_SCALE_FACTOR"] = str(scale_factor)
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
else:
    print(f"DEBUG: Standard resolution display. No scaling applied.")

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from .app import KioskApp

def main():
    # Allow imports from parent dir if needed for models etc (though kiosk shouldn't use models directly)
    # sys.path.append(...)
    
    print(f"DEBUG: Startup Args: {sys.argv}")
    args = list(sys.argv) # Safe copy
    
    print("DEBUG: Init QApplication...")
    qt_app = QApplication(args)
    
    # Verify the detected resolution via Qt
    screen = qt_app.primaryScreen()
    rect = screen.geometry()
    print(f"DEBUG: Qt reports screen resolution: {rect.width()}x{rect.height()}")
    
    # Hide Cursor for Touchscreen Kiosk
    qt_app.setOverrideCursor(Qt.CursorShape.BlankCursor)
    
    print("DEBUG: Init KioskApp (Loading Views)...")
    try:
        window = KioskApp()
    except Exception as e:
        print(f"CRITICAL: Failed to launch KioskApp: {e}")
        import traceback
        traceback.print_exc()
        
        # EMERGENCY MODE
        from PySide6.QtWidgets import QLabel, QMainWindow
        window = QMainWindow()
        window.setWindowTitle("FATAL ERROR")
        lbl = QLabel(f"FATAL STARTUP ERROR:\n{e}\n\nCheck logs locally.")
        lbl.setStyleSheet("background: red; color: white; font-size: 24px; padding: 50px;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        window.setCentralWidget(lbl)
    
    print("DEBUG: KioskApp Ready (or Failed).")
    
    if "--fullscreen" in args:
        print("DEBUG: Mode = Fullscreen")
        # Force geometry to match screen (fix for no-WM environments)
        screen = qt_app.primaryScreen()
        rect = screen.geometry()
        print(f"Detected Screen: {rect.width()}x{rect.height()}")
        
        # In bare X11, showFullScreen() can be flaky. 
        # We manually set it to frameless and fill the screen.
        window.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        window.move(0, 0)
        window.resize(rect.width(), rect.height())
        window.show()
    else:
        print("Starting in Windowed Mode")
        window.show()
    
    sys.exit(qt_app.exec())

if __name__ == "__main__":
    main()
