
from PySide6.QtGui import QFontDatabase, QGuiApplication
import os
import sys

app = QGuiApplication(sys.argv)
font_dir = "kiosk/assets/fonts"
print(f"Checking fonts in {font_dir}...")

for f in os.listdir(font_dir):
    if f.endswith(".ttf"):
        path = os.path.join(font_dir, f)
        idx = QFontDatabase.addApplicationFont(path)
        if idx < 0:
            print(f"❌ Failed to load {f}")
        else:
            families = QFontDatabase.applicationFontFamilies(idx)
            print(f"✅ Loaded {f} -> Families: {families}")
            
print("Done.")
