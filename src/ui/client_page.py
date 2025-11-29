# src/ui/client_page.py
from src.ui.admin_page import APP_STYLE
from PyQt5 import QtGui
from PyQt5 import QtWidgets, QtCore
import json
import datetime
from bson import ObjectId

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
        """
        Builds the client UI with a left side menu and a stacked area:
        - Bookings (default)
        - Stats (client booking statistics)
        - Usage (last 30 days)
        - Spending (per facility)
        """
        # outer layout: horizontal (side menu + main stack)
        outer = QtWidgets.QHBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)

        # ----------------- Side menu -----------------
        self.side_menu = QtWidgets.QListWidget()
        self.side_menu.setFixedWidth(180)
        self.side_menu.addItem("My Bookings")
        self.side_menu.addItem("Stats")
        self.side_menu.addItem("Usage")
        self.side_menu.addItem("Spending")
        self.side_menu.setCurrentRow(0)  # default
        outer.addWidget(self.side_menu)

        # ----------------- Stacked area -----------------
        self.stack = QtWidgets.QStackedWidget()
        outer.addWidget(self.stack, 1)

        # -------- page 0: bookings (reuse existing table + detail) --------
        bookings_page = QtWidgets.QWidget()
        bp_layout = QtWidgets.QVBoxLayout(bookings_page)

        # header (welcome, refresh, new, cancel, logout)
        header = QtWidgets.QHBoxLayout()
        welcome = QtWidgets.QLabel(f"Welcome, {self.member.get('firstName','')}")
        welcome.setStyleSheet("font-size:16pt; font-weight:700;")
        header.addWidget(welcome)
        header.addStretch()

        # keep/restore buttons used previously
        self.btn_refresh = QtWidgets.QPushButton("Refresh")
        self.btn_new_booking = QtWidgets.QPushButton("New Booking")
        self.btn_cancel_booking = QtWidgets.QPushButton("Cancel Booking")
        self.btn_logout = QtWidgets.QPushButton("Logout")
        self.btn_check_in = QtWidgets.QPushButton("Check-In")
        self.btn_check_out = QtWidgets.QPushButton("Check-Out")
        self.btn_notifications = QtWidgets.QPushButton("Notifications") 
        header.addWidget(self.btn_refresh)
        header.addWidget(self.btn_new_booking)
        header.addWidget(self.btn_cancel_booking)
        header.addWidget(self.btn_logout)
        header.addWidget(self.btn_check_in)
        header.addWidget(self.btn_check_out)
        header.addWidget(self.btn_notifications)

        bp_layout.addLayout(header)

        # bookings table
        self.table = QtWidgets.QTableWidget()
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        bp_layout.addWidget(self.table, 1)

        # details area
        self.detail = QtWidgets.QPlainTextEdit()
        self.detail.setReadOnly(True)
        self.detail.setFixedHeight(160)
        bp_layout.addWidget(self.detail)

        self.stack.addWidget(bookings_page)

        # -------- page 1: Stats --------
        stats_page = QtWidgets.QWidget()
        s_layout = QtWidgets.QVBoxLayout(stats_page)
        stats_header = QtWidgets.QLabel("Your Booking Statistics")
        stats_header.setStyleSheet("font-weight:700; font-size:14pt;")
        s_layout.addWidget(stats_header)
        # stat labels container
        self.lbl_total_bookings = QtWidgets.QLabel("Total bookings: -")
        self.lbl_status_counts = QtWidgets.QLabel("By status: -")
        self.lbl_total_paid = QtWidgets.QLabel("Total paid: -")
        self.lbl_top_facility = QtWidgets.QLabel("Most used facility: -")
        for w in (self.lbl_total_bookings, self.lbl_status_counts, self.lbl_total_paid, self.lbl_top_facility):
            w.setStyleSheet("font-size:11pt; padding:6px;")
            s_layout.addWidget(w)
        s_layout.addStretch()
        self.stack.addWidget(stats_page)

        # -------- page 2: Usage (table) --------
        usage_page = QtWidgets.QWidget()
        u_layout = QtWidgets.QVBoxLayout(usage_page)
        u_header = QtWidgets.QLabel("Usage (last 30 days)")
        u_header.setStyleSheet("font-weight:700; font-size:14pt;")
        u_layout.addWidget(u_header)
        self.usage_table = QtWidgets.QTableWidget()
        u_layout.addWidget(self.usage_table, 1)
        self.stack.addWidget(usage_page)

        # -------- page 3: Spending per facility (table) --------
        spending_page = QtWidgets.QWidget()
        sp_layout = QtWidgets.QVBoxLayout(spending_page)
        sp_header = QtWidgets.QLabel("Spending by Facility")
        sp_header.setStyleSheet("font-weight:700; font-size:14pt;")
        sp_layout.addWidget(sp_header)
        self.spending_table = QtWidgets.QTableWidget()
        sp_layout.addWidget(self.spending_table, 1)
        self.stack.addWidget(spending_page)

        # ----------------- Connect signals -----------------
        self.side_menu.currentRowChanged.connect(self._on_side_selected)
        self.btn_refresh.clicked.connect(self._load_bookings)
        self.btn_new_booking.clicked.connect(self._on_new_booking_clicked)
        self.btn_cancel_booking.clicked.connect(self._on_cancel_booking)
        self.btn_logout.clicked.connect(self._on_logout_clicked)
        self.table.itemSelectionChanged.connect(self._on_row_selected)
        self.btn_check_in.clicked.connect(self._on_check_in_clicked)
        self.btn_check_out.clicked.connect(self._on_check_out_clicked)
        self.btn_notifications.clicked.connect(self._on_show_notifications)

        # set default view to My Bookings
        self.stack.setCurrentIndex(0)


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
        Create a logout notification and call the logout callback (or just close).
        """
        try:
            # create logout notification
            try:
                notif = {
                    "memberId": self.member.get("_id"),
                    "type": "logout",
                    "title": "Logged out",
                    "message": f"You logged out at {datetime.datetime.utcnow().isoformat()}",
                    "sentAt": datetime.datetime.utcnow(),
                    "status": "sent"
                }
                self.db.insert_doc("notifications", notif)
            except Exception:
                pass

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
                res=self.db.insert_doc("bookings", doc)
                try:
                    notif = {
                        "memberId": self.member.get("_id"),
                        "bookingId": res.inserted_id,
                        "type": "booking_created",
                        "title": "Booking Created",
                        "message": f"Your booking on {doc.get('startTime')} has been created (status: {doc.get('status')}).",
                        "sentAt": datetime.datetime.utcnow(),
                        "status": "sent"
                    }
                    self.db.insert_doc("notifications", notif)
                except Exception:
                    # non-critical; ignore notification errors
                    pass
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
            # create notification for the member
            try:
                notif = {
                    "memberId": self.member.get("_id"),
                    "bookingId": _id,
                    "type": "booking_cancelled",
                    "title": "Booking Cancelled",
                    "message": f"Your booking (id: {_id}) was cancelled.",
                    "sentAt": datetime.datetime.utcnow(),
                    "status": "sent"
                }
                self.db.insert_doc("notifications", notif)
            except Exception:
                pass

            QtWidgets.QMessageBox.information(self, "Cancelled", f"Modified: {getattr(res,'modified_count', '?')}")
            self._load_bookings()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Cancel failed", str(e))


    def _on_side_selected(self, index):
        """
        When side menu selection changes, switch the stack page and trigger load actions.
        0: My Bookings, 1: Stats, 2: Usage, 3: Spending
        """
        self.stack.setCurrentIndex(index)
        if index == 0:
            self._load_bookings()
        elif index == 1:
            self._load_client_stats()
        elif index == 2:
            self._load_usage_trends()
        elif index == 3:
            self._load_spending_by_facility()


    def _load_client_stats(self):
        """Populate the small stats labels using aggregations on bookings."""
        member_id = self.member.get("_id")
        if member_id is None:
            return

        # 1) Total bookings
        try:
            res = list(self.db.db["bookings"].aggregate([
                {"$match": {"memberId": member_id}},
                {"$count": "totalBookings"}
            ]))
            total = res[0]["totalBookings"] if res else 0
        except Exception:
            total = 0
        self.lbl_total_bookings.setText(f"Total bookings: {total}")

        # 2) Counts by status
        try:
            res = list(self.db.db["bookings"].aggregate([
                {"$match": {"memberId": member_id}},
                {"$group": {"_id": "$status", "count": {"$sum": 1}}}
            ]))
            pairs = [f"{r['_id']}: {r['count']}" for r in res]
            status_text = ", ".join(pairs) if pairs else "None"
        except Exception:
            status_text = "Error"
        self.lbl_status_counts.setText(f"By status: {status_text}")

        # 3) Total paid
        try:
            res = list(self.db.db["bookings"].aggregate([
                {"$match": {"memberId": member_id, "payment.amount": {"$exists": True}}},
                {"$group": {"_id": None, "totalPaid": {"$sum": "$payment.amount"}}}
            ]))
            total_paid = res[0]["totalPaid"] if res else 0
        except Exception:
            total_paid = 0
        self.lbl_total_paid.setText(f"Total paid: {total_paid}")

        # 4) Most used facility (get facility name)
        try:
            res = list(self.db.db["bookings"].aggregate([
                {"$match": {"memberId": member_id}},
                {"$group": {"_id": "$facilityId", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 1}
            ]))
            top_fid = res[0]["_id"] if res else None
            if top_fid:
                fac = self.db.db["facilities"].find_one({"_id": top_fid})
                top_name = fac.get("name") if fac else str(top_fid)
            else:
                top_name = "—"
        except Exception:
            top_name = "Error"
        self.lbl_top_facility.setText(f"Most used facility: {top_name}")


    def _load_usage_trends(self):
        """
        Load usageLogs for last 30 days and fill usage_table with columns: day, totalMinutes
        """
        member_id = self.member.get("_id")
        if member_id is None:
            return

        # compute 30 days ago
        thirty_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=30)

        try:
            pipeline = [
                {"$match": {"memberId": member_id, "checkIn": {"$gte": thirty_days_ago}}},
                {"$project": {
                    "day": {"$dateToString": {"format": "%Y-%m-%d", "date": "$checkIn"}},
                    "minutes": {"$ifNull": ["$durationMinutes", 0]}
                }},
                {"$group": {"_id": "$day", "totalMinutes": {"$sum": "$minutes"}}},
                {"$sort": {"_id": 1}}
            ]
            res = list(self.db.db["usageLogs"].aggregate(pipeline))
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Aggregation error", str(e))
            res = []

        # populate table
        if not res:
            self.usage_table.clear(); self.usage_table.setRowCount(0); self.usage_table.setColumnCount(0)
            return

        self.usage_table.setColumnCount(2)
        self.usage_table.setRowCount(len(res))
        self.usage_table.setHorizontalHeaderLabels(["day", "totalMinutes"])
        for r, row in enumerate(res):
            day_item = QtWidgets.QTableWidgetItem(str(row["_id"]))
            mins_item = QtWidgets.QTableWidgetItem(str(row["totalMinutes"]))
            self.usage_table.setItem(r, 0, day_item)
            self.usage_table.setItem(r, 1, mins_item)
        self.usage_table.resizeColumnsToContents()


    def _load_spending_by_facility(self):
        """
        Aggregate total payment.amount per facility for this client and show in spending_table.
        """
        member_id = self.member.get("_id")
        if member_id is None:
            return

        try:
            pipeline = [
                {"$match": {"memberId": member_id, "payment.amount": {"$exists": True}}},
                {"$group": {"_id": "$facilityId", "totalSpent": {"$sum": "$payment.amount"}}},
                {"$sort": {"totalSpent": -1}}
            ]
            res = list(self.db.db["bookings"].aggregate(pipeline))
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Aggregation error", str(e))
            res = []

        if not res:
            self.spending_table.clear(); self.spending_table.setRowCount(0); self.spending_table.setColumnCount(0)
            return

        # map facility ids to names in batch
        fac_ids = [r["_id"] for r in res if r["_id"] is not None]
        fac_map = {}
        if fac_ids:
            try:
                facs = list(self.db.db["facilities"].find({"_id": {"$in": fac_ids}}))
                for f in facs:
                    fac_map[f["_id"]] = f.get("name") or str(f["_id"])
            except Exception:
                fac_map = {}

        self.spending_table.setColumnCount(2)
        self.spending_table.setRowCount(len(res))
        self.spending_table.setHorizontalHeaderLabels(["facility", "totalSpent"])
        for r, row in enumerate(res):
            fid = row["_id"]
            name = fac_map.get(fid, str(fid))
            self.spending_table.setItem(r, 0, QtWidgets.QTableWidgetItem(str(name)))
            self.spending_table.setItem(r, 1, QtWidgets.QTableWidgetItem(str(row["totalSpent"])))
        self.spending_table.resizeColumnsToContents()


    def _on_check_in_clicked(self):
        """
        Create a new usageLogs entry for the selected booking (or ask user to pick a booking).
        Fields: memberId, facilityId, checkIn (datetime), sessionStatus = 'in_progress'
        """
        sel = self.table.selectedItems()
        if not sel:
            QtWidgets.QMessageBox.warning(self, "No selection", "Select a booking (row) to check in.")
            return
        row = sel[0].row()
        booking = self.table.item(row, 0).data(QtCore.Qt.UserRole)
        if not booking:
            QtWidgets.QMessageBox.warning(self, "No document", "Could not retrieve the booking.")
            return

        member_id = self.member.get("_id")
        facility_id = booking.get("facilityId")
        if facility_id is None:
            QtWidgets.QMessageBox.warning(self, "Missing facility", "Selected booking has no facilityId.")
            return

        # confirm
        ok = QtWidgets.QMessageBox.question(self, "Confirm check-in",
                                            "Create a check-in record for this booking?",
                                            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if ok != QtWidgets.QMessageBox.Yes:
            return

        now = datetime.datetime.utcnow()
        usage_doc = {
            "memberId": member_id,
            "facilityId": facility_id,
            "checkIn": now,
            "sessionStatus": "in_progress",
            # checkOut and durationMinutes will be added on checkout
        }
        try:
            res = self.db.insert_doc("usageLogs", usage_doc)
            # notification
            try:
                notif = {
                    "memberId": self.member.get("_id"),
                    "bookingId": booking.get("_id"),
                    "type": "checked_in",
                    "title": "Checked In",
                    "message": f"Checked in to {booking.get('startTime')} / facility {booking.get('facilityId')}.",
                    "sentAt": datetime.datetime.utcnow(),
                    "status": "sent"
                }
                self.db.insert_doc("notifications", notif)
            except Exception:
                pass
            QtWidgets.QMessageBox.information(self, "Checked in", f"Check-in recorded (id: {res.inserted_id}).")
            # optionally refresh usage view or bookings list
            # self._load_usage_trends()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Insert failed", str(e))


    def _on_check_out_clicked(self):
        """
        Complete the latest in_progress usageLog for the selected booking's facility and the current member:
        - set checkOut (now)
        - compute durationMinutes (rounded to minutes)
        - set sessionStatus = 'completed'
        """
        sel = self.table.selectedItems()
        if not sel:
            QtWidgets.QMessageBox.warning(self, "No selection", "Select the booking row you want to check out from.")
            return
        row = sel[0].row()
        booking = self.table.item(row, 0).data(QtCore.Qt.UserRole)
        if not booking:
            QtWidgets.QMessageBox.warning(self, "No document", "Could not retrieve the booking.")
            return

        member_id = self.member.get("_id")
        facility_id = booking.get("facilityId")
        if facility_id is None:
            QtWidgets.QMessageBox.warning(self, "Missing facility", "Selected booking has no facilityId.")
            return

        # find the most recent in_progress usageLog for this member & facility
        try:
            query = {"memberId": member_id, "facilityId": facility_id, "sessionStatus": "in_progress"}
            doc = self.db.db["usageLogs"].find_one(query, sort=[("checkIn", -1)])
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "DB error", str(e))
            return

        if not doc:
            QtWidgets.QMessageBox.information(self, "No open session", "No in-progress check-in found for this facility.")
            return

        # confirm checkout
        ok = QtWidgets.QMessageBox.question(self, "Confirm check-out",
                                            "Complete the session and record check-out?",
                                            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if ok != QtWidgets.QMessageBox.Yes:
            return

        now = datetime.datetime.utcnow()
        checkin_time = doc.get("checkIn")
        # compute duration in minutes (round to nearest int)
        duration_minutes = None
        try:
            if isinstance(checkin_time, datetime.datetime):
                delta = now - checkin_time
                duration_minutes = int(round(delta.total_seconds() / 60.0))
            else:
                # if stored as string, try parsing ISO
                try:
                    parsed = datetime.datetime.fromisoformat(str(checkin_time))
                    delta = now - parsed
                    duration_minutes = int(round(delta.total_seconds() / 60.0))
                except Exception:
                    duration_minutes = None
        except Exception:
            duration_minutes = None

        update = {
            "checkOut": now,
            "sessionStatus": "completed"
        }
        if duration_minutes is not None:
            update["durationMinutes"] = duration_minutes

        try:
            # update the usageLogs doc by its _id
            self.db.update_doc("usageLogs", doc["_id"], update)
            # notification
            try:
                notif = {
                    "memberId": self.member.get("_id"),
                    "bookingId": booking.get("_id"),
                    "type": "checked_out",
                    "title": "Checked Out",
                    "message": f"Checked out. Duration: {duration_minutes if duration_minutes is not None else 'N/A'} minutes.",
                    "sentAt": datetime.datetime.utcnow(),
                    "status": "sent"
                }
                self.db.insert_doc("notifications", notif)
            except Exception:
                pass
            QtWidgets.QMessageBox.information(self, "Checked out",
                                            f"Session completed. Duration: {duration_minutes if duration_minutes is not None else 'N/A'} minutes.")
            # Optionally refresh usage/booking views
            # self._load_usage_trends()
            # self._load_bookings()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Update failed", str(e))


    def _on_show_notifications(self):
        """
        Show a dialog listing notifications for the current member.
        Allows marking selected notifications as 'read'.
        """
        member_id = self.member.get("_id")
        if member_id is None:
            return

        # fetch notifications sorted newest first
        try:
            docs = list(self.db.db["notifications"].find({"memberId": member_id}).sort("sentAt", -1).limit(200))
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "DB Error", f"Failed to load notifications: {e}")
            return

        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("Notifications")
        dlg.resize(560, 420)
        v = QtWidgets.QVBoxLayout(dlg)

        listw = QtWidgets.QListWidget()
        for n in docs:
            sent = n.get("sentAt")
            ts = str(sent) if sent is not None else ""
            title = n.get("title", n.get("type", "notification"))
            msg = n.get("message", "")
            status = n.get("status", "sent")
            display = f"[{status}] {ts} — {title}: {msg}"
            item = QtWidgets.QListWidgetItem(display)
            item.setData(QtCore.Qt.UserRole, n)  # store full doc
            listw.addItem(item)

        v.addWidget(listw)

        # buttons: mark read, close
        h = QtWidgets.QHBoxLayout()
        btn_mark = QtWidgets.QPushButton("Mark selected as read")
        btn_close = QtWidgets.QPushButton("Close")
        h.addStretch()
        h.addWidget(btn_mark)
        h.addWidget(btn_close)
        v.addLayout(h)

        def on_close():
            dlg.accept()

        def on_mark_read():
            sel = listw.selectedItems()
            if not sel:
                QtWidgets.QMessageBox.information(dlg, "No selection", "Select notifications to mark as read.")
                return
            ids = []
            for it in sel:
                n = it.data(QtCore.Qt.UserRole)
                if n and n.get("_id"):
                    ids.append(n["_id"])
            # update each to status = "read"
            try:
                for _id in ids:
                    self.db.update_doc("notifications", _id, {"status": "read"})
                QtWidgets.QMessageBox.information(dlg, "Updated", f"Marked {len(ids)} notifications as read.")
                # refresh list in dialog
                new_docs = list(self.db.db["notifications"].find({"memberId": member_id}).sort("sentAt", -1).limit(200))
                listw.clear()
                for n in new_docs:
                    sent = n.get("sentAt"); ts = str(sent) if sent is not None else ""
                    title = n.get("title", n.get("type", "notification"))
                    msg = n.get("message", "")
                    status = n.get("status", "sent")
                    display = f"[{status}] {ts} — {title}: {msg}"
                    item = QtWidgets.QListWidgetItem(display)
                    item.setData(QtCore.Qt.UserRole, n)
                    listw.addItem(item)
            except Exception as e:
                QtWidgets.QMessageBox.critical(dlg, "Update failed", str(e))

        btn_close.clicked.connect(on_close)
        btn_mark.clicked.connect(on_mark_read)

        dlg.exec_()


