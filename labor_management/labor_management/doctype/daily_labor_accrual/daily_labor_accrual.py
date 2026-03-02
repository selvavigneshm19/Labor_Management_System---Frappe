# Copyright (c) 2026, FlexiDigit and contributors
# For license information, please see license.txt

# Copyright (c) 2026, FlexiDigit and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DailyLaborAccrual(Document):

    def validate(self):
        # Prevent duplicate accrual for same attendance
        self.prevent_duplicate_accrual()

        # Pull attendance data & calculate costs
        self.pull_attendance_data()

    def prevent_duplicate_accrual(self):
        """
        BUSINESS RULE:
        One Attendance → One Daily Labor Accrual
        """
        if not self.attendance:
            return

        existing = frappe.db.exists(
            "Daily Labor Accrual",
            {
                "attendance": self.attendance,
                "name": ["!=", self.name],
                "docstatus": ["!=", 2]  # not cancelled
            }
        )

        if existing:
            frappe.throw(
                f"Daily Labor Accrual already exists for Attendance {self.attendance}"
            )

    def pull_attendance_data(self):
        """
        Pull data from Labor Attendance V2
        and auto-calculate costs
        """
        if not self.attendance:
            return

        # Clear old lines (important during edit)
        self.set("accrual_lines", [])

        attendance = frappe.get_doc("Labor Attendance V2", self.attendance)

        total_present = 0
        total_ot_hours = 0
        total_cost = 0

        for row in attendance.attendance_lines:
            line = self.append("accrual_lines", {})
            line.labor_staff = row.labor_staff
            line.present_count = row.present_count or 0
            line.ot_hours = row.ot_hours or 0
            line.rate = row.rate or 0

            # Cost calculation
            line.line_cost = (
                (line.present_count * line.rate) +
                (line.ot_hours * line.rate)
            )

            total_present += line.present_count
            total_ot_hours += line.ot_hours
            total_cost += line.line_cost

        # Set summary totals
        self.total_present = total_present
        self.total_ot_hours = total_ot_hours
        self.total_cost = total_cost

    def on_submit(self):
        """
        Lock the accrual once submitted
        """
        self.db_set("accrual_status", "Posted")

    def on_cancel(self):
        """
        Mark accrual as cancelled
        """
        self.db_set("accrual_status", "Cancelled")
