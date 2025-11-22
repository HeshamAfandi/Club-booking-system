# main.py (project root)
import sys
from PyQt5 import QtWidgets
from src.core.db_client import DBClient
from src.ui.login import LoginWindow

def main():
    app = QtWidgets.QApplication(sys.argv)
    db = DBClient()
    win = LoginWindow(db)
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
