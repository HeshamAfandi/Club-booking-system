# src/ui/admin_page.py
import json
from PyQt5 import QtWidgets, QtCore
from src.core.services import preview_text


COLLECTION_ORDER = ["membershipLevels","members","facilities","bookings","usageLogs","notifications"]

class AdminPage(QtWidgets.QWidget):
    def __init__(self, dbclient):
        super().__init__()
        self.db = dbclient
        self.docs_cache = []
        self.setWindowTitle("Club Booking — Admin")
        self.resize(1000, 600)
        self._build_ui()
        self.load_collections()

    def _build_ui(self):
        layout = QtWidgets.QHBoxLayout(self)
        # left list
        left = QtWidgets.QVBoxLayout()
        left.addWidget(QtWidgets.QLabel("Collections"))
        self.coll_list = QtWidgets.QListWidget()
        left.addWidget(self.coll_list)
        self.btn_refresh = QtWidgets.QPushButton("Refresh")
        left.addWidget(self.btn_refresh)
        layout.addLayout(left, 1)

        # center docs preview
        center = QtWidgets.QVBoxLayout()
        center.addWidget(QtWidgets.QLabel("Documents"))
        self.docs_list = QtWidgets.QListWidget()
        center.addWidget(self.docs_list, 1)
        btns = QtWidgets.QHBoxLayout()
        self.btn_load = QtWidgets.QPushButton("Load")
        self.btn_insert = QtWidgets.QPushButton("Insert JSON")
        self.btn_delete = QtWidgets.QPushButton("Delete")
        btns.addWidget(self.btn_load); btns.addWidget(self.btn_insert); btns.addWidget(self.btn_delete)
        center.addLayout(btns)
        layout.addLayout(center, 2)

        # right JSON viewer
        right = QtWidgets.QVBoxLayout()
        right.addWidget(QtWidgets.QLabel("JSON"))
        self.json_view = QtWidgets.QPlainTextEdit(); self.json_view.setReadOnly(True)
        right.addWidget(self.json_view, 1)
        layout.addLayout(right, 3)

        # signals
        self.coll_list.currentItemChanged.connect(self.on_collection_selected)
        self.btn_refresh.clicked.connect(self.load_collections)
        self.btn_load.clicked.connect(self.load_docs)
        self.docs_list.currentItemChanged.connect(self.on_doc_selected)
        self.btn_insert.clicked.connect(self.on_insert)
        self.btn_delete.clicked.connect(self.on_delete)

    def load_collections(self):
        self.coll_list.clear()
        available = self.db.list_collections()
        for name in COLLECTION_ORDER:
            if name in available:
                self.coll_list.addItem(name)
        for name in available:
            if name not in COLLECTION_ORDER:
                self.coll_list.addItem(name)
        if self.coll_list.count() > 0:
            self.coll_list.setCurrentRow(0)

    def on_collection_selected(self, cur, prev):
        self.docs_list.clear()
        self.json_view.clear()

    def load_docs(self):
        cur = self.coll_list.currentItem()
        if not cur: return
        coll = cur.text()
        docs = self.db.find_docs(coll)
        self.docs_cache = docs
        self.docs_list.clear()
        for d in docs:
            self.docs_list.addItem(preview_text(d))

    def on_doc_selected(self, item):
        i = self.docs_list.currentRow()
        if i < 0: return
        doc = self.docs_cache[i]
        try:
            pretty = json.dumps(self._convert(doc), indent=2, default=str)
        except Exception:
            pretty = str(doc)
        self.json_view.setPlainText(pretty)

    def on_insert(self):
        cur = self.coll_list.currentItem()
        if not cur: return
        coll = cur.text()
        text, ok = QtWidgets.QInputDialog.getMultiLineText(self, "Insert JSON", f"Insert into {coll}", "{}")
        if not ok: return
        try:
            doc = json.loads(text)
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "JSON error", str(e)); return
        try:
            self.db.insert_doc(coll, doc)
            QtWidgets.QMessageBox.information(self, "Inserted", "Document inserted.")
            self.load_docs()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Insert failed", str(e))

    def on_delete(self):
        idx = self.docs_list.currentRow()
        if idx < 0: return
        doc = self.docs_cache[idx]
        ok = QtWidgets.QMessageBox.question(self, "Confirm", "Delete selected document?")
        if ok != QtWidgets.QMessageBox.Yes: return
        try:
            self.db.delete_doc(self.coll_list.currentItem().text(), doc["_id"])
            QtWidgets.QMessageBox.information(self, "Deleted", "Document deleted.")
            self.load_docs()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Delete failed", str(e))

    def _convert(self, obj):
        if isinstance(obj, dict):
            return {k: self._convert(v) for k,v in obj.items()}
        if isinstance(obj, list):
            return [self._convert(v) for v in obj]
        try:
            return str(obj)
        except:
            return obj
