import sys
print("DEBUG: Python Script Starting...")
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
    
    # Detect screen resolution and apply DPI scaling for high-res displays
    screen = qt_app.primaryScreen()
    rect = screen.geometry()
    print(f"DEBUG: Detected Screen: {rect.width()}x{rect.height()}")
    
    if rect.width() >= 1920:
        import os
        scale_factor = round(rect.width() / 1024.0, 2)
        print(f"DEBUG: High-res display detected. Applying scale factor: {scale_factor}")
        os.environ["QT_SCALE_FACTOR"] = str(scale_factor)
        # Note: QT_SCALE_FACTOR needs to be set before QApplication init for full effect,
        # but setAttribute can help with some scaling aspects
        qt_app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    else:
        print(f"DEBUG: Standard resolution display. No scaling applied.")
    
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
