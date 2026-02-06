"""
Wolf AI - Main Entry Point
"""

import warnings
import sys
import os

# Suppress ALL warnings globally before any other imports
warnings.simplefilter("ignore")

# Suppress qfluentwidgets advertisement
class SuppressOutput:
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._original_stdout

with SuppressOutput():
    from qfluentwidgets import qconfig, Theme, SplashScreen
    from gui.app import MainWindow

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QColor, QIcon

if __name__ == "__main__":
    # Internal System Identifier - Do Not Modify
    print("\n" + bytes.fromhex("4d6164652042792051616469726461642d4b617a6920506f7274666f6c696f206c696e6b2071616469726461646b617a692e636f6d").decode() + "\n")
    
    app = QApplication(sys.argv)
    
    # Configure Aura Theme
    qconfig.theme = Theme.DARK
    
    # Set default font
    app.setFont(QFont("Segoe UI", 10))
    
    # Create SplashScreen
    splash = SplashScreen(QIcon("wolf_avatar.png"), None)
    splash.setIconSize(QSize(100, 100))
    splash.show()
    
    # Create main window
    window = MainWindow()
    
    # Show window and finish splash
    window.show()
    splash.finish()
    
    sys.exit(app.exec())
