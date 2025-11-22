# src/ui/client_page.py
from src.ui.admin_page import APP_STYLE
from PyQt5 import QtGui
from PyQt5 import QtWidgets, QtCore
import json

class ClientPage(QtWidgets.QWidget):
    def __init__(self, dbclient, member, logout_callback=None):
        super().__init__()
        self.db = dbclient
        self.member = member
        self.logout_callback = logout_callback
        self._build_ui()
        self.setStyleSheet(APP_STYLE)
        # set global font similar to admin
        base_font = QtGui.QFont()
        base_font.setPointSize(13)
        base_font.setFamily("Segoe UI")
        self.setFont(base_font)

        self.setWindowTitle(f"Club Booking — Client ({self.member.get('firstName','')})")
        self.resize(1000, 600)
        # load member bookings
        self._load_bookings()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        header = QtWidgets.QHBoxLayout()
        welcome = QtWidgets.QLabel(f"Welcome, {self.member.get('firstName','')}")
        welcome.setStyleSheet("font-size:16pt; font-weight:700;")
        header.addWidget(welcome)
        header.addStretch()
        self.btn_refresh = QtWidgets.QPushButton("Refresh")
        self.btn_logout = QtWidgets.QPushButton("Logout")
        header.addWidget(self.btn_refresh)
        header.addWidget(self.btn_logout)
        layout.addLayout(header)

        # bookings table
        self.table = QtWidgets.QTableWidget()
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.table, 1)

        # details area
        self.detail = QtWidgets.QPlainTextEdit()
        self.detail.setReadOnly(True)
        self.detail.setFixedHeight(160)
        layout.addWidget(self.detail)

        # signals
        self.btn_refresh.clicked.connect(self._load_bookings)
        self.table.itemSelectionChanged.connect(self._on_row_selected)
        self.btn_logout.clicked.connect(self._on_logout_clicked)

    def _load_bookings(self):
        member_id = self.member.get("_id")
        try:
            docs = list(self.db.db["bookings"].find({"memberId": member_id}).limit(500))
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "DB Error", f"Failed to load bookings: {e}")
            return

        if not docs:
            self.table.clear(); self.table.setRowCount(0); self.table.setColumnCount(0)
            self.detail.setPlainText("No bookings found.")
            return

        # derive columns simply
        keys = []
        preferred = ["_id", "facilityId", "startTime", "endTime", "durationMinutes", "status"]
        for k in preferred:
            if any(k in d for d in docs):
                keys.append(k)
        for d in docs:
            for k in d.keys():
                if k not in keys:
                    keys.append(k)

        self.table.setColumnCount(len(keys)); self.table.setRowCount(len(docs))
        self.table.setHorizontalHeaderLabels(keys)
        for r, d in enumerate(docs):
            for c, k in enumerate(keys):
                val = d.get(k, "")
                text = json.dumps(val, default=str) if isinstance(val, (dict, list)) else str(val)
                item = QtWidgets.QTableWidgetItem(text)
                if c == 0:
                    item.setData(QtCore.Qt.UserRole, d)
                self.table.setItem(r, c, item)
        self.table.resizeColumnsToContents()

    def _on_row_selected(self):
        sel = self.table.selectedItems()
        if not sel:
            self.detail.setPlainText("")
            return
        row = sel[0].row()
        doc = self.table.item(row, 0).data(QtCore.Qt.UserRole)
        try:
            pretty = json.dumps(doc, default=str, indent=2)
        except Exception:
            pretty = str(doc)
        self.detail.setPlainText(pretty)

    def _on_logout_clicked(self):
        """
        Call the logout callback if provided, otherwise just close the client page.
        """
        try:
            if callable(getattr(self, "logout_callback", None)):
                self.logout_callback()
        finally:
            self.close()
