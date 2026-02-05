import traceback
import sys
from PySide6.QtWidgets import QApplication
app = QApplication([])

try:
    from gui.tabs.settings import SettingsTab
    print("Import successful")
    t = SettingsTab()
    print("SettingsTab created")
    print("Layout count:", t.expandLayout.count())
except Exception as e:
    traceback.print_exc()
    sys.exit(1)
