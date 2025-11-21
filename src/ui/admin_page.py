# src/ui/admin_page.py
"""
Modern Admin Page for Club Booking (PyQt5)
- Replaces previous admin_page.py
- Left: large collection buttons (6 collections)
- Center: TableView with flattened columns (no JSON shown)
- Right: Details panel (key/value)
- Theme: dark modern style
- Updated: adjusted table font size and fixed last-row white/selection rendering
"""

import json
from PyQt5 import QtWidgets, QtGui, QtCore
from src.core.services import preview_text  # small helper (already in services.py)

COLLECTIONS = ["membershipLevels", "members", "facilities", "bookings", "usageLogs", "notifications"]
MAX_ROWS = 200

# ---------- Small helper to flatten values for table cells ----------
def flatten_for_cell(value, max_len=120):
    """Return a short readable string for nested types."""
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        try:
            s = json.dumps(value, default=str)
        except Exception:
            s = str(value)
        # shorten long JSON
        if len(s) > max_len:
            return s[:max_len-3] + "..."
        return s
    return str(value)

# ---------- Stylesheet (modern dark) ----------
APP_STYLE = """
QWidget {
    background: #0f1115;
    color: #E6EEF3;
    font-family: "Segoe UI", Roboto, Arial;
    font-size: 12px;
}

/* Buttons and left panel */
QPushButton {
    background: transparent;
    border: none;
    color: #cfe8ff;
    padding: 8px;
    text-align: left;
}
QPushButton:hover { background: rgba(255,255,255,0.03); }
QPushButton:pressed { background: rgba(255,255,255,0.04); }

QListWidget, QPlainTextEdit {
    background: #0b0c0f;
    border: 1px solid rgba(255,255,255,0.04);
}

/* Table styling - make font bigger and fix background colors */
QTableWidget {
    background-color: #07121a; /* table viewport background */
    color: #E6EEF3;
    border: 1px solid rgba(255,255,255,0.03);
    font-size: 13.5pt;  /* increased table font size for readability */
}

/* Make alternate rows slightly different but never white */
QTableWidget::item {
    padding: 6px;
    background-color: transparent; /* let the row background show */
}
QTableWidget::item:selected {
    background: #113255;
    color: #eaf6ff;
}

/* Use explicit row background colors via palette via the widget; fallback colors */
QTableView::item:alternate {
    background: rgba(255,255,255,0.015);
}

/* Header */
QHeaderView::section {
    background: #0b0c0f;
    color: #bfe0ff;
    padding: 6px;
    border: none;
    font-weight: 700;
    font-size: 12.5pt;
}

/* Left panel */
#leftPanel {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #091220, stop:1 #07121a);
    border-right: 1px solid rgba(255,255,255,0.03);
}
.collectionButton {
    font-size: 13px;
    padding: 12px;
    margin: 6px;
    border-radius: 6px;
    color: #dbeeff;
}
.collectionButton[selected="true"] {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #1f6fff, stop:1 #0ea5ff);
    color: white;
    font-weight: 700;
}

/* Details */
.detailKey {
    color: #98b7d9;
    font-weight: 700;
}
.detailValue {
    color: #e5f0ff;
}
"""

# ---------- Main UI Widget ----------
class AdminPage(QtWidgets.QWidget):
    def __init__(self, dbclient):
        super().__init__()
        self.db = dbclient
        self.current_collection = None
        self.docs_cache = []  # current page docs
        self._build_ui()
        self.setStyleSheet(APP_STYLE)
        # default load first collection if available
        QtCore.QTimer.singleShot(50, self._initial_load)

    def _initial_load(self):
        # refresh collection list and auto-select first
        self.load_collections()
        if self.left_buttons and len(self.left_buttons) > 0:
            self._on_collection_clicked(COLLECTIONS[0])

    def _build_ui(self):
        self.setWindowTitle("Club Booking — Admin (Modern)")
        self.resize(1200, 700)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Left panel: collection buttons
        left = QtWidgets.QFrame()
        left.setObjectName("leftPanel")
        left.setFixedWidth(200)
        left_layout = QtWidgets.QVBoxLayout(left)
        left_layout.setContentsMargins(8, 8, 8, 8)
        left_layout.addSpacing(8)
        header = QtWidgets.QLabel("Collections")
        header.setStyleSheet("font-weight:800; font-size:14px; color:#dff0ff; padding-left:8px;")
        left_layout.addWidget(header)
        left_layout.addSpacing(6)

        self.left_buttons = []
        for name in COLLECTIONS:
            b = QtWidgets.QPushButton(name)
            b.setObjectName(name)
            b.setProperty("class", "collectionButton")
            b.setProperty("selected", False)
            b.clicked.connect(lambda _, n=name: self._on_collection_clicked(n))
            left_layout.addWidget(b)
            self.left_buttons.append(b)

        left_layout.addStretch()
        layout.addWidget(left)

        # Center: topbar + table
        center_frame = QtWidgets.QFrame()
        center_layout = QtWidgets.QVBoxLayout(center_frame)
        center_layout.setContentsMargins(12, 12, 12, 12)

        # Top bar (search / refresh / insert / delete)
        topbar = QtWidgets.QHBoxLayout()
        topbar.setSpacing(8)
        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText("Quick search (will filter table columns)...")
        self.search_input.setFixedHeight(34)
        self.btn_search = QtWidgets.QPushButton("Search")
        self.btn_refresh = QtWidgets.QPushButton("Refresh")
        self.btn_insert = QtWidgets.QPushButton("Insert")
        self.btn_delete = QtWidgets.QPushButton("Delete")
        for w in (self.btn_search, self.btn_refresh, self.btn_insert, self.btn_delete):
            w.setFixedHeight(34)

        topbar.addWidget(self.search_input, 1)
        topbar.addWidget(self.btn_search)
        topbar.addWidget(self.btn_refresh)
        topbar.addWidget(self.btn_insert)
        topbar.addWidget(self.btn_delete)
        center_layout.addLayout(topbar)

        # Table
        self.table = QtWidgets.QTableWidget()
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(False)
        self.table.setStyleSheet("""
            QTableWidget { background-color: #07121a; }
            QTableWidget::item { background: transparent; }
            QTableWidget::item:selected { background: #113255; color: #eaf6ff; }
        """)
        center_layout.addWidget(self.table, 1)
        layout.addWidget(center_frame, 3)

        # Right: details panel
        right_frame = QtWidgets.QFrame()
        right_frame.setFixedWidth(360)
        right_layout = QtWidgets.QVBoxLayout(right_frame)
        right_layout.setContentsMargins(12, 12, 12, 12)
        lbl = QtWidgets.QLabel("Details")
        lbl.setStyleSheet("font-weight:700; font-size:14px; color:#dff0ff;")
        right_layout.addWidget(lbl)
        right_layout.addSpacing(6)

        self.detail_scroll = QtWidgets.QScrollArea()
        self.detail_scroll.setWidgetResizable(True)
        self.detail_container = QtWidgets.QWidget()
        self.detail_vbox = QtWidgets.QVBoxLayout(self.detail_container)
        self.detail_vbox.setAlignment(QtCore.Qt.AlignTop)
        self.detail_scroll.setWidget(self.detail_container)
        right_layout.addWidget(self.detail_scroll, 1)

        # small helper: show count
        self.count_label = QtWidgets.QLabel("")
        self.count_label.setStyleSheet("color:#9ec0db;")
        right_layout.addWidget(self.count_label)

        layout.addWidget(right_frame)

        # signals
        self.table.itemSelectionChanged.connect(self._on_table_selection_changed)
        self.btn_refresh.clicked.connect(self._on_refresh_clicked)
        self.btn_search.clicked.connect(self._on_search_clicked)
        self.btn_insert.clicked.connect(self._on_insert_clicked)
        self.btn_delete.clicked.connect(self._on_delete_clicked)

    # ---------- UI handlers ----------
    def load_collections(self):
        # if user created others, we keep order of COLLECTIONS at top
        existing = self.db.list_collections()
        # highlight available ones only
        for b in self.left_buttons:
            if b.objectName() in existing:
                b.setEnabled(True)
            else:
                b.setEnabled(False)

    def _on_collection_clicked(self, name):
        # update button selected state
        for b in self.left_buttons:
            b.setProperty("selected", b.objectName() == name)
            b.setStyle(b.style())  # refresh style
        self.current_collection = name
        self._load_docs(name)

    def _load_docs(self, coll):
        # load docs (limit)
        try:
            docs = self.db.find_docs(coll, limit=MAX_ROWS)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "DB Error", f"Failed to load {coll}:\n{e}")
            return
        self.docs_cache = docs
        self._populate_table(docs)
        self.count_label.setText(f"Showing {len(docs)} documents (max {MAX_ROWS})")

    def _populate_table(self, docs):
        # derive columns from union of keys but try to prioritize simple fields
        if not docs:
            self.table.clear()
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            return
        # choose a stable order: prefer common keys
        preferred = ["_id", "name", "firstName", "lastName", "email", "type", "status", "startTime", "endTime", "sentAt"]
        keys = []
        for k in preferred:
            if any(k in d for d in docs):
                keys.append(k)
        # then add remaining keys in encountered order
        for d in docs:
            for k in d.keys():
                if k not in keys:
                    keys.append(k)
        # set up table
        self.table.setColumnCount(len(keys))
        self.table.setRowCount(len(docs))
        self.table.setHorizontalHeaderLabels(keys)
        # ensure the model uses a stable palette to avoid white artifacts
        palette = self.table.palette()
        palette.setColor(QtGui.QPalette.Base, QtGui.QColor("#07121a"))
        self.table.setPalette(palette)

        for r, d in enumerate(docs):
            for c, k in enumerate(keys):
                val = d.get(k, "")
                cell_text = flatten_for_cell(val)
                item = QtWidgets.QTableWidgetItem(cell_text)
                # store full doc on first column for retrieval
                if c == 0:
                    item.setData(QtCore.Qt.UserRole, d)
                self.table.setItem(r, c, item)
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)

    def _on_table_selection_changed(self):
        sel = self.table.selectedItems()
        if not sel:
            self._show_details(None)
            return
        row = sel[0].row()
        item = self.table.item(row, 0)
        doc = item.data(QtCore.Qt.UserRole)
        self._show_details(doc)

    def _show_details(self, doc):
        # clear current details
        for i in reversed(range(self.detail_vbox.count())):
            w = self.detail_vbox.itemAt(i).widget()
            if w:
                w.deleteLater()
        if not doc:
            self.detail_vbox.addWidget(QtWidgets.QLabel("No document selected"))
            return
        # show each key/value in readable form
        for k, v in doc.items():
            key_lbl = QtWidgets.QLabel(str(k))
            key_lbl.setProperty("class", "detailKey")
            key_lbl.setStyleSheet("padding-top:8px;")
            val_lbl = QtWidgets.QLabel(flatten_for_cell(v, max_len=1000))
            val_lbl.setWordWrap(True)
            val_lbl.setStyleSheet("padding-bottom:6px;")
            # small layout
            self.detail_vbox.addWidget(key_lbl)
            self.detail_vbox.addWidget(val_lbl)
        # spacer
        self.detail_vbox.addStretch()

    # ---------- actions ----------
    def _on_refresh_clicked(self):
        if self.current_collection:
            self._load_docs(self.current_collection)
        else:
            self.load_collections()

    def _on_search_clicked(self):
        q = self.search_input.text().strip()
        if not self.current_collection:
            return
        if not q:
            self._load_docs(self.current_collection)
            return
        # naive client-side filter: find q in flattened string of any field
        filtered = []
        for d in self.docs_cache:
            found = False
            for v in d.values():
                if q.lower() in flatten_for_cell(v).lower():
                    found = True
                    break
            if found:
                filtered.append(d)
        self._populate_table(filtered)
        self.count_label.setText(f"Filtered: {len(filtered)}")

    def _on_insert_clicked(self):
        # small JSON dialog to insert — keep DB logic same as before
        if not self.current_collection:
            QtWidgets.QMessageBox.warning(self, "No Collection", "Select a collection first.")
            return
        text, ok = QtWidgets.QInputDialog.getMultiLineText(self, "Insert Document (JSON)",
                                                           f"Insert into {self.current_collection}", "{}")
        if not ok:
            return
        try:
            doc = json.loads(text)
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "JSON error", f"Invalid JSON: {e}")
            return
        try:
            res = self.db.insert_doc(self.current_collection, doc)
            QtWidgets.QMessageBox.information(self, "Inserted", f"Inserted id: {res.inserted_id}")
            self._load_docs(self.current_collection)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Insert failed", str(e))

    def _on_delete_clicked(self):
        # delete currently selected document
        sel = self.table.selectedItems()
        if not sel:
            QtWidgets.QMessageBox.warning(self, "No selection", "Select a row to delete.")
            return
        row = sel[0].row()
        item = self.table.item(row, 0)
        doc = item.data(QtCore.Qt.UserRole)
        ok = QtWidgets.QMessageBox.question(self, "Confirm Delete",
                                            f"Delete document {_short_id(doc.get('_id'))}?")
        if ok != QtWidgets.QMessageBox.Yes:
            return
        try:
            self.db.delete_doc(self.current_collection, doc["_id"])
            QtWidgets.QMessageBox.information(self, "Deleted", "Document deleted.")
            self._load_docs(self.current_collection)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Delete failed", str(e))

# small util
def _short_id(oid):
    try:
        return str(oid)
    except:
        return repr(oid)
