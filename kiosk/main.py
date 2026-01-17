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
        window.showFullScreen()
    else:
        print("Starting in Windowed Mode")
        window.show()
    
    sys.exit(qt_app.exec())

if __name__ == "__main__":
    main()
