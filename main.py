# src/ui/main.py
import sys
from PyQt5 import QtWidgets
from src.core.db_client import DBClient
from src.ui.admin_page import AdminPage


def main():
    app = QtWidgets.QApplication(sys.argv)
    db = DBClient()   # uses src/core/config.py
    win = AdminPage(db)
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
