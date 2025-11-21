"""
club_booking_gui.py
Phase 2 prototype: GUI + MongoDB connection for Clubs Booking System.

Features:
- Connects to MongoDB via MONGO_URI environment variable or interactive input.
- Ensures database + collections exist using your Phase1 schema (no changes).
- Seeds a small sample dataset.
- GUI shows collections list, documents table, detail view, and CRUD buttons.
- Database operations run in a QThread to keep UI responsive.

Requirements:
    pip install pymongo pyqt5
"""

import os
import sys
import json
import datetime
from functools import partial

from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, DuplicateKeyError

from PyQt5 import QtWidgets, QtCore, QtGui

from dotenv import load_dotenv

load_dotenv()

# ---------- Configuration ----------
DB_NAME = "club_booking_db"  # name for Phase 2 DB
COLLECTIONS = [
    "membershipLevels",
    "members",
    "facilities",
    "bookings",
    "usageLogs",
    "notifications",
]
# -----------------------------------


# ----- Database layer (simple wrapper) -----
class DBClient:
    def __init__(self, uri):
        self.client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        # Will raise on first call to server if unreachable
        self.db = self.client[DB_NAME]

    def ping(self):
        return self.client.admin.command("ping")

    def ensure_collections(self):
        # Create collections if missing and create basic indexes
        for coll in COLLECTIONS:
            if coll not in self.db.list_collection_names():
                self.db.create_collection(coll)
        # Example index: members.email unique
        try:
            self.db.members.create_index("email", unique=True)
        except Exception:
            pass

    def seed_sample_data(self):
        """Insert small sample documents only if collections empty."""
        if self.db.membershipLevels.count_documents({}) == 0:
            levels = [
                {"name": "Basic", "maxBookingsPerDay": 1, "advanceBookingWindowDays": 7,
                 "accessibleFacilityTypes": ["gym"], "price": 100},
                {"name": "Premium", "maxBookingsPerDay": 3, "advanceBookingWindowDays": 30,
                 "accessibleFacilityTypes": ["gym", "pool", "court"], "price": 300},
            ]
            self.db.membershipLevels.insert_many(levels)

        if self.db.facilities.count_documents({}) == 0:
            facs = [
                {"name": "Gym A", "type": "gym", "status": "available", "maintenanceNote": "",
                 "bookedSlots": [], "assignedStaff": [{"name": "Ahmed", "role": "manager", "contact": "010..." }],
                 "openingHours": [{"day": "Mon", "open": "06:00", "close": "22:00"}]},
                {"name": "Pool 1", "type": "pool", "status": "maintenance", "maintenanceNote": "Cleaning",
                 "bookedSlots": [], "assignedStaff": [{"name": "Mona", "role": "lifeguard", "contact": "011..." }],
                 "openingHours": [{"day": "Tue", "open": "08:00", "close": "20:00"}]},
            ]
            self.db.facilities.insert_many(facs)

        if self.db.members.count_documents({}) == 0:
            # find a membershipLevel id
            lvl = self.db.membershipLevels.find_one({"name": "Basic"})
            member = {"firstName": "Hesham", "lastName": "El Afandi", "email": "hesham@example.com",
                      "phone": "01000000000", "membershipLevelId": lvl["_id"], "status": "active",
                      "activeBookingsCount": 0}
            try:
                self.db.members.insert_one(member)
            except DuplicateKeyError:
                pass

    def list_collections(self):
        return COLLECTIONS

    def find_docs(self, collection, filter=None, limit=200):
        filter = filter or {}
        cursor = self.db[collection].find(filter).limit(limit)
        return list(cursor)

    def find_one(self, collection, _id):
        return self.db[collection].find_one({"_id": _id})

    def insert_doc(self, collection, doc):
        return self.db[collection].insert_one(doc)

    def update_doc(self, collection, _id, update_doc):
        return self.db[collection].update_one({"_id": _id}, {"$set": update_doc})

    def delete_doc(self, collection, _id):
        return self.db[collection].delete_one({"_id": _id})


# ----- Worker thread for DB operations -----
class DBWorker(QtCore.QThread):
    resultReady = QtCore.pyqtSignal(object, object)  # (action, payload)
    error = QtCore.pyqtSignal(str)

    def __init__(self, dbclient, parent=None):
        super().__init__(parent)
        self.db = dbclient
        self._task = None

    def run(self):
        if not self._task:
            return
        action = self._task.get("action")
        try:
            if action == "ping":
                r = self.db.ping()
                self.resultReady.emit("ping", r)
            elif action == "ensure":
                self.db.ensure_collections()
                self.db.seed_sample_data()
                self.resultReady.emit("ensure", True)
            elif action == "list_docs":
                coll = self._task["collection"]
                docs = self.db.find_docs(coll)
                # convert ObjectId to str for UI convenience
                for d in docs:
                    if "_id" in d:
                        d["_id_str"] = str(d["_id"])
                self.resultReady.emit("list_docs", {"collection": coll, "docs": docs})
            elif action == "insert":
                coll = self._task["collection"]
                doc = self._task["doc"]
                res = self.db.insert_doc(coll, doc)
                self.resultReady.emit("insert", {"collection": coll, "inserted_id": str(res.inserted_id)})
            elif action == "delete":
                coll = self._task["collection"]
                _id = self._task["_id"]
                res = self.db.delete_doc(coll, _id)
                self.resultReady.emit("delete", {"collection": coll, "deleted_count": res.deleted_count})
            elif action == "update":
                coll = self._task["collection"]
                _id = self._task["_id"]
                update = self._task["update"]
                res = self.db.update_doc(coll, _id, update)
                self.resultReady.emit("update", {"collection": coll, "modified_count": res.modified_count})
        except ServerSelectionTimeoutError as e:
            self.error.emit("DB connection failed: " + str(e))
        except Exception as e:
            self.error.emit("DB error: " + str(e))

    def set_task(self, task):
        self._task = task


# ----- GUI -----
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, dbclient):
        super().__init__()
        self.setWindowTitle("Club Booking Admin - Phase2")
        self.resize(1000, 600)
        self.dbclient = dbclient
        self.worker = DBWorker(self.dbclient)
        self.worker.resultReady.connect(self.on_worker_result)
        self.worker.error.connect(self.on_worker_error)

        self._setup_ui()
        self._connect_signals()

        # initialize DB (ensure collections + seed)
        self.run_db_task({"action": "ensure"})

    def _setup_ui(self):
        main = QtWidgets.QWidget()
        self.setCentralWidget(main)
        h = QtWidgets.QHBoxLayout(main)

        # Left: collections list
        left = QtWidgets.QVBoxLayout()
        self.coll_list = QtWidgets.QListWidget()
        self.coll_list.addItems(COLLECTIONS)
        left.addWidget(QtWidgets.QLabel("Collections"))
        left.addWidget(self.coll_list, 1)

        # Buttons for refresh/seed
        btns = QtWidgets.QHBoxLayout()
        self.btn_refresh = QtWidgets.QPushButton("Refresh")
        self.btn_seed = QtWidgets.QPushButton("Seed Sample")
        btns.addWidget(self.btn_refresh)
        btns.addWidget(self.btn_seed)
        left.addLayout(btns)

        h.addLayout(left, 1)

        # Center: documents table
        center = QtWidgets.QVBoxLayout()
        center.addWidget(QtWidgets.QLabel("Documents"))
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(0)
        self.table.setRowCount(0)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        center.addWidget(self.table, 1)

        # CRUD buttons
        crud = QtWidgets.QHBoxLayout()
        self.btn_new = QtWidgets.QPushButton("New")
        self.btn_edit = QtWidgets.QPushButton("Edit")
        self.btn_delete = QtWidgets.QPushButton("Delete")
        crud.addWidget(self.btn_new); crud.addWidget(self.btn_edit); crud.addWidget(self.btn_delete)
        center.addLayout(crud)

        h.addLayout(center, 3)

        # Right: detail JSON view
        right = QtWidgets.QVBoxLayout()
        right.addWidget(QtWidgets.QLabel("Document JSON"))
        self.text_json = QtWidgets.QPlainTextEdit()
        self.text_json.setReadOnly(True)
        right.addWidget(self.text_json, 1)

        # Search / filter
        right.addWidget(QtWidgets.QLabel("Filter (JSON)"))
        self.filter_input = QtWidgets.QLineEdit("{}")
        self.btn_apply_filter = QtWidgets.QPushButton("Apply Filter")
        frow = QtWidgets.QHBoxLayout()
        frow.addWidget(self.filter_input)
        frow.addWidget(self.btn_apply_filter)
        right.addLayout(frow)

        h.addLayout(right, 2)

    def _connect_signals(self):
        self.coll_list.currentItemChanged.connect(self.on_collection_selected)
        self.btn_refresh.clicked.connect(self.on_refresh_clicked)
        self.btn_seed.clicked.connect(lambda: self.run_db_task({"action": "ensure"}))
        self.table.itemSelectionChanged.connect(self.on_table_selection_changed)

        self.btn_new.clicked.connect(self.on_new_clicked)
        self.btn_edit.clicked.connect(self.on_edit_clicked)
        self.btn_delete.clicked.connect(self.on_delete_clicked)
        self.btn_apply_filter.clicked.connect(self.on_apply_filter)

    # ----- UI event handlers -----
    def on_collection_selected(self, current, previous):
        if current:
            coll = current.text()
            self.load_collection(coll)

    def on_refresh_clicked(self):
        item = self.coll_list.currentItem()
        if item:
            self.load_collection(item.text())

    def on_table_selection_changed(self):
        sel = self.table.selectedItems()
        if not sel:
            self.text_json.clear()
            return
        row = sel[0].row()
        # show JSON of the first column's doc stored in Qt.UserRole
        item = self.table.item(row, 0)
        doc = item.data(QtCore.Qt.UserRole)
        try:
            pretty = json.dumps(self._convert_bson_for_ui(doc), default=str, indent=2)
        except Exception:
            pretty = str(doc)
        self.text_json.setPlainText(pretty)

    def on_new_clicked(self):
        item = self.coll_list.currentItem()
        if not item:
            QtWidgets.QMessageBox.warning(self, "No collection", "Please select a collection first.")
            return
        coll = item.text()
        # open a JSON editor dialog with a sensible default (empty object)
        text, ok = QtWidgets.QInputDialog.getMultiLineText(self, "New document (JSON)", f"Insert into {coll}", "{}")
        if ok:
            try:
                doc = json.loads(text)
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "JSON error", str(e))
                return
            self.run_db_task({"action": "insert", "collection": coll, "doc": doc})

    def on_edit_clicked(self):
        item = self._selected_item()
        if not item:
            QtWidgets.QMessageBox.warning(self, "Select", "Select a document to edit.")
            return
        coll = self.coll_list.currentItem().text()
        doc = item.data(QtCore.Qt.UserRole)
        # remove _id for editing convenience (we update by original _id)
        doc_to_edit = dict(doc)
        if "_id" in doc_to_edit:
            doc_to_edit.pop("_id")
        text, ok = QtWidgets.QInputDialog.getMultiLineText(self, "Edit document (JSON)", f"Edit {coll}", json.dumps(self._convert_bson_for_ui(doc_to_edit), default=str, indent=2))
        if ok:
            try:
                update_doc = json.loads(text)
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "JSON error", str(e))
                return
            self.run_db_task({"action": "update", "collection": coll, "_id": doc["_id"], "update": update_doc})

    def on_delete_clicked(self):
        item = self._selected_item()
        if not item:
            QtWidgets.QMessageBox.warning(self, "Select", "Select a document to delete.")
            return
        coll = self.coll_list.currentItem().text()
        doc = item.data(QtCore.Qt.UserRole)
        ok = QtWidgets.QMessageBox.question(self, "Confirm delete", "Delete selected document?")
        if ok == QtWidgets.QMessageBox.Yes:
            self.run_db_task({"action": "delete", "collection": coll, "_id": doc["_id"]})

    def on_apply_filter(self):
        item = self.coll_list.currentItem()
        if not item:
            return
        coll = item.text()
        try:
            flt = json.loads(self.filter_input.text() or "{}")
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Filter JSON", f"Invalid JSON: {e}")
            return
        # call find with filter (we do a simple implementation by setting a special task)
        # For simplicity reusing list_docs and applying filter client-side:
        docs = list(self.dbclient.find_docs(coll, filter=flt))
        for d in docs:
            if "_id" in d:
                d["_id_str"] = str(d["_id"])
        self.populate_table(coll, docs)

    # ----- helpers -----
    def _selected_item(self):
        sel = self.table.selectedItems()
        if not sel:
            return None
        row = sel[0].row()
        return self.table.item(row, 0)

    def load_collection(self, coll):
        self.run_db_task({"action": "list_docs", "collection": coll})

    def populate_table(self, collection, docs):
        # Determine columns by union of keys in docs (excluding nested objects => present JSON only)
        if not docs:
            self.table.clear()
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            return
        # choose visible keys (give priority to _id, simple fields)
        keys = []
        for d in docs:
            for k in d.keys():
                if k not in keys:
                    keys.append(k)
        # show readable str for _id
        self.table.setColumnCount(len(keys))
        self.table.setRowCount(len(docs))
        self.table.setHorizontalHeaderLabels(keys)
        for r, d in enumerate(docs):
            for c, k in enumerate(keys):
                val = d.get(k, "")
                disp = val
                # convert ObjectId or nested structures to readable string
                if k == "_id" or k.endswith("Id"):
                    disp = str(val)
                elif isinstance(val, (dict, list)):
                    try:
                        disp = json.dumps(self._convert_bson_for_ui(val), default=str)
                    except Exception:
                        disp = str(val)
                else:
                    disp = str(val)
                item = QtWidgets.QTableWidgetItem(disp)
                item.setData(QtCore.Qt.UserRole, d)  # store the full doc on first column items
                self.table.setItem(r, c, item)

        self.table.resizeColumnsToContents()

    def _convert_bson_for_ui(self, obj):
        # recursively convert ObjectId to str and datetimes to ISO
        if isinstance(obj, dict):
            return {k: self._convert_bson_for_ui(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_bson_for_ui(v) for v in obj]
        elif hasattr(obj, "isoformat"):
            return obj.isoformat()
        else:
            try:
                return str(obj)
            except Exception:
                return obj

    # ----- worker interactions -----
    def run_db_task(self, task):
        self.worker.set_task(task)
        if self.worker.isRunning():
            self.worker.wait()
        self.worker.start()

    def on_worker_result(self, action, payload):
        if action == "ensure":
            # reload collection list UI (not necessary) and select first
            if self.coll_list.count() > 0:
                self.coll_list.setCurrentRow(0)
        elif action == "list_docs":
            coll = payload["collection"]
            docs = payload["docs"]
            self.populate_table(coll, docs)
        elif action == "insert":
            QtWidgets.QMessageBox.information(self, "Inserted", f"Inserted id: {payload['inserted_id']}")
            self.on_refresh_clicked()
        elif action == "delete":
            QtWidgets.QMessageBox.information(self, "Deleted", f"Deleted: {payload['deleted_count']}")
            self.on_refresh_clicked()
        elif action == "update":
            QtWidgets.QMessageBox.information(self, "Updated", f"Modified: {payload['modified_count']}")
            self.on_refresh_clicked()
        elif action == "ping":
            pass

    def on_worker_error(self, msg):
        QtWidgets.QMessageBox.critical(self, "DB Error", msg)


# ---------- Startup ----------
def main():
    # Get Mongo URI (env or prompt)
    uri = os.getenv("MONGO_URI")
    if not uri:
        # prompt user for Mongo URI
        app_temp = QtWidgets.QApplication(sys.argv)
        uri, ok = QtWidgets.QInputDialog.getText(None, "MongoDB URI", "Enter MongoDB URI (e.g. mongodb://localhost:27017):")
        if not ok or not uri:
            QtWidgets.QMessageBox.critical(None, "No URI", "MongoDB URI is required. Set MONGO_URI env var or input one.")
            return
    try:
        dbclient = DBClient(uri)
        dbclient.ping()
    except Exception as e:
        QtWidgets.QMessageBox.critical(None, "DB Connection", f"Failed to connect to MongoDB: {e}")
        return

    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow(dbclient)
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
