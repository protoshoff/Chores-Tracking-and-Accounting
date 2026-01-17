import sys
from PySide6.QtWidgets import QApplication
from .app import KioskApp

def main():
    # Allow imports from parent dir if needed for models etc (though kiosk shouldn't use models directly)
    # sys.path.append(...)
    
    qt_app = QApplication(sys.argv)
    window = KioskApp()
    
    if "--fullscreen" in sys.argv:
        print("Starting in Fullscreen Mode")
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
