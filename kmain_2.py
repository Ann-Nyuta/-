import sys
from PyQt6.QtWidgets import QApplication
from login_2 import LoginWindow
from database_2 import Database

if __name__ == "__main__":
    app = QApplication(sys.argv)
    db = Database()

    login_window = LoginWindow()
    login_window.show()

    sys.exit(app.exec())