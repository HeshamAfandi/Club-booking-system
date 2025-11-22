# src/ui/login.py
from PyQt5 import QtWidgets, QtCore
import json

# import existing pages
from src.ui.admin_page import AdminPage
from src.ui.client_page import ClientPage

class LoginWindow(QtWidgets.QWidget):
    def __init__(self, dbclient):
        super().__init__()
        self.db = dbclient
        self._build_ui()
        self.setWindowTitle("Club Booking — Login")
        self.resize(420, 200)

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        header = QtWidgets.QLabel("Sign in")
        header.setStyleSheet("font-size:18pt; font-weight:700; padding:6px;")
        layout.addWidget(header)

        form = QtWidgets.QFormLayout()
        self.first_input = QtWidgets.QLineEdit()
        self.first_input.setPlaceholderText("First name (use firstName)")
        self.pw_input = QtWidgets.QLineEdit()
        self.pw_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.pw_input.setPlaceholderText("Password (member.password)")

        form.addRow("First name:", self.first_input)
        form.addRow("Password:", self.pw_input)
        layout.addLayout(form)

        btns = QtWidgets.QHBoxLayout()
        self.btn_login = QtWidgets.QPushButton("Login")
        self.btn_quit = QtWidgets.QPushButton("Quit")
        btns.addStretch()
        btns.addWidget(self.btn_login)
        btns.addWidget(self.btn_quit)
        layout.addLayout(btns)

        self.btn_login.clicked.connect(self._on_login)
        self.btn_quit.clicked.connect(QtWidgets.QApplication.quit)

    def _on_login(self):
        name = self.first_input.text().strip()
        pw = self.pw_input.text()

        if not name or not pw:
            QtWidgets.QMessageBox.warning(self, "Missing", "Please enter first name and password.")
            return

        # --- HARD-CODED ADMIN LOGIN ---
        if name.lower() == "admin" and pw == "admin123":
            self.admin_win = AdminPage(self.db, logout_callback=self._open_new_login)
            self.admin_win.show()
            self.close()
            return
        # ----------------------------------------------------------

        # --- NORMAL USER LOGIN (members collection) ---
        try:
            member = self.db.db["members"].find_one({"firstName": name, "password": pw})
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "DB error", f"Failed to query members: {e}")
            return

        if not member:
            QtWidgets.QMessageBox.warning(self, "Unauthorized", "Invalid credentials.")
            return

        # open client page (member)
        self.client_win = ClientPage(self.db, member, logout_callback=self._open_new_login)
        self.client_win.show()
        self.close()


    def _open_new_login(self):
        # create and show a new LoginWindow tied to same DB
        new_login = LoginWindow(self.db)
        new_login.show()
