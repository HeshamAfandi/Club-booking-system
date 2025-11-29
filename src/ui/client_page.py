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
        self.btn_new_booking = QtWidgets.QPushButton("New Booking")
        self.btn_cancel_booking = QtWidgets.QPushButton("Cancel Booking")
        self.btn_logout = QtWidgets.QPushButton("Logout")
        header.addWidget(self.btn_refresh)
        header.addWidget(self.btn_new_booking)
        header.addWidget(self.btn_cancel_booking)
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
        self.btn_new_booking.clicked.connect(self._on_new_booking_clicked)
        self.btn_cancel_booking.clicked.connect(self._on_cancel_booking)

    def _load_bookings(self):
        """
        Load bookings for the logged-in member and display a friendly table:
        columns: facilityName, startTime, endTime, durationMinutes, status, paymentSummary
        No _id, no memberId, no facilityId shown.
        """
        member_id = self.member.get("_id")
        try:
            # fetch bookings for member
            docs = list(self.db.db["bookings"].find({"memberId": member_id}).limit(500))
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "DB Error", f"Failed to load bookings: {e}")
            return

        if not docs:
            self.table.clear(); self.table.setRowCount(0); self.table.setColumnCount(0)
            self.detail.setPlainText("No bookings found.")
            return

        # Build a set of facilityIds present, then fetch their names once
        facility_ids = set()
        for d in docs:
            fid = d.get("facilityId")
            if fid is not None:
                facility_ids.add(fid)

        facility_map = {}
        if facility_ids:
            try:
                # fetch facility docs for mapping _id -> name
                facs = list(self.db.db["facilities"].find({"_id": {"$in": list(facility_ids)}}))
                for f in facs:
                    facility_map[f.get("_id")] = f.get("name") or str(f.get("_id"))
            except Exception:
                # fallback: leave map empty (we'll show id as string)
                facility_map = {}

        # Decide columns to show (friendly)
        columns = ["facilityName", "startTime", "endTime", "durationMinutes", "status", "payment"]
        self.table.setColumnCount(len(columns))
        self.table.setRowCount(len(docs))
        self.table.setHorizontalHeaderLabels(columns)

        for r, d in enumerate(docs):
            # facility name resolution
            fid = d.get("facilityId")
            facility_name = facility_map.get(fid, str(fid) if fid is not None else "")
            cell_values = {
                "facilityName": facility_name,
                "startTime": d.get("startTime", ""),
                "endTime": d.get("endTime", ""),
                "durationMinutes": d.get("durationMinutes", ""),
                "status": d.get("status", ""),
                "payment": ""
            }
            # payment summary (if exists)
            p = d.get("payment")
            if isinstance(p, dict):
                # short summary: amount + status if available
                amt = p.get("amount")
                st = p.get("status")
                if amt is not None and st:
                    cell_values["payment"] = f"{amt} ({st})"
                elif amt is not None:
                    cell_values["payment"] = str(amt)
                elif st:
                    cell_values["payment"] = st
                else:
                    cell_values["payment"] = ""
            else:
                # if still raw value or None
                cell_values["payment"] = "" if p is None else str(p)

            for c, col in enumerate(columns):
                text = str(cell_values.get(col, ""))
                item = QtWidgets.QTableWidgetItem(text)
                # keep the full booking doc linked to the first column for selection/details
                if c == 0:
                    item.setData(QtCore.Qt.UserRole, d)
                self.table.setItem(r, c, item)

        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)


    def _on_row_selected(self):
        """
        When a booking row is selected show a readable details JSON but
        hide '_id', 'memberId' and 'facilityId' so client doesn't see raw ids.
        """
        sel = self.table.selectedItems()
        if not sel:
            self.detail.setPlainText("")
            return
        row = sel[0].row()
        booking_doc = self.table.item(row, 0).data(QtCore.Qt.UserRole)
        if not booking_doc:
            self.detail.setPlainText("")
            return

        # make a shallow copy and remove ID fields before pretty-printing
        doc_for_display = dict(booking_doc)  # shallow copy
        for remove_key in ("_id", "memberId", "facilityId"):
            if remove_key in doc_for_display:
                doc_for_display.pop(remove_key, None)

        # attempt to pretty print
        try:
            pretty = json.dumps(doc_for_display, default=str, indent=2)
        except Exception:
            pretty = str(doc_for_display)
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

    def _on_new_booking_clicked(self):
        """Open the Create Booking dialog for current member."""
        self._show_create_booking_dialog()

    def _show_create_booking_dialog(self):
        """
        Simple dialog to create a new booking for the logged-in member.
        Fields: facility (dropdown), startTime (ISO), endTime (ISO), payment method + amount (optional).
        """
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("New Booking")
        dialog.setModal(True)
        form = QtWidgets.QFormLayout()

        # facility combo (load once)
        combo = QtWidgets.QComboBox()
        try:
            fac_docs = list(self.db.db["facilities"].find({}).limit(1000))
            combo.addItem("-- choose facility --", None)
            for f in fac_docs:
                combo.addItem(str(f.get("name") or f.get("_id")), f.get("_id"))
        except Exception as e:
            combo.addItem("Error loading facilities", None)

        start_input = QtWidgets.QLineEdit()
        start_input.setPlaceholderText("e.g. 2025-11-21T09:00:00")
        end_input = QtWidgets.QLineEdit()
        end_input.setPlaceholderText("e.g. 2025-11-21T10:00:00")

        # Payment inputs
        payment_method = QtWidgets.QComboBox()
        payment_method.addItem("none", None)
        payment_method.addItem("cash", "cash")
        payment_method.addItem("credit_card", "credit_card")
        payment_method.addItem("bank_transfer", "bank_transfer")
        payment_method.addItem("wallet", "wallet")
        payment_amount = QtWidgets.QLineEdit()
        payment_amount.setPlaceholderText("Optional: amount (e.g. 120)")

        form.addRow("Facility", combo)
        form.addRow("Start (ISO)", start_input)
        form.addRow("End (ISO)", end_input)
        form.addRow("Payment method", payment_method)
        form.addRow("Payment amount", payment_amount)

        # buttons
        btn_box = QtWidgets.QHBoxLayout()
        btn_box.addStretch()
        ok_btn = QtWidgets.QPushButton("Create")
        cancel_btn = QtWidgets.QPushButton("Cancel")
        btn_box.addWidget(cancel_btn)
        btn_box.addWidget(ok_btn)

        vbox = QtWidgets.QVBoxLayout(dialog)
        vbox.addLayout(form)
        vbox.addLayout(btn_box)

        def on_cancel():
            dialog.reject()

        def coerce_number(s):
            s = s.strip()
            if s == "":
                return None
            try:
                if "." in s:
                    return float(s)
                return int(s)
            except Exception:
                return s  # fallback to string if cannot convert

        def on_create():
            facility_id = combo.currentData()
            start = start_input.text().strip()
            end = end_input.text().strip()
            pm = payment_method.currentData()
            pa_raw = payment_amount.text().strip()

            if facility_id is None:
                QtWidgets.QMessageBox.warning(dialog, "Missing", "Please choose a facility.")
                return
            if not start or not end:
                QtWidgets.QMessageBox.warning(dialog, "Missing", "Please provide start and end times.")
                return

            doc = {
                "memberId": self.member.get("_id"),
                "facilityId": facility_id,
                "startTime": start,
                "endTime": end,
                "status": "pending",
            }

            # assemble payment object only if provided
            payment_obj = {}
            has_payment = False
            if pm is not None:
                # method selected that's not "none"
                payment_obj["method"] = pm
                has_payment = True
            if pa_raw != "":
                amt = coerce_number(pa_raw)
                payment_obj["amount"] = amt
                has_payment = True

            if has_payment:
                # optionally you can add default payment.status or paidAt here
                doc["payment"] = payment_obj

            try:
                self.db.insert_doc("bookings", doc)
                QtWidgets.QMessageBox.information(dialog, "Created", "Booking created successfully.")
                dialog.accept()
                self._load_bookings()
            except Exception as e:
                QtWidgets.QMessageBox.critical(dialog, "Insert failed", str(e))

        cancel_btn.clicked.connect(on_cancel)
        ok_btn.clicked.connect(on_create)

        dialog.exec_()


    def _on_cancel_booking(self):
        """Cancel (soft-cancel) the selected booking by setting status='cancelled'."""
        sel = self.table.selectedItems()
        if not sel:
            QtWidgets.QMessageBox.warning(self, "No selection", "Select a booking to cancel.")
            return
        row = sel[0].row()
        booking = self.table.item(row, 0).data(QtCore.Qt.UserRole)
        if not booking:
            QtWidgets.QMessageBox.warning(self, "No document", "Could not retrieve the booking.")
            return

        # confirm
        ret = QtWidgets.QMessageBox.question(self, "Confirm cancel",
                                            "Are you sure you want to cancel this booking?",
                                            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if ret != QtWidgets.QMessageBox.Yes:
            return

        try:
            _id = booking.get("_id")
            if _id is None:
                QtWidgets.QMessageBox.critical(self, "Cancel failed", "_id missing; cannot cancel.")
                return
            # perform a soft-cancel (set status)
            res = self.db.update_doc("bookings", _id, {"status": "cancelled"})
            QtWidgets.QMessageBox.information(self, "Cancelled", f"Modified: {getattr(res,'modified_count', '?')}")
            self._load_bookings()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Cancel failed", str(e))

