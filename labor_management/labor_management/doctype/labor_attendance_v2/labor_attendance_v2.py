# Copyright (c) 2026, FlexiDigit
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class LaborAttendanceV2(Document):

    def validate(self):
        self.set_vendor_warehouse_from_mdm()
        self.validate_duplicate_attendance()
        self.calculate_attendance_summary()

    # ------------------------------------------------------------
    # AUTO CREATE DAILY LABOR ACCRUAL ON SUBMIT
    # ------------------------------------------------------------
    def on_submit(self):
        self.create_daily_labor_accrual()

    def create_daily_labor_accrual(self):
        # Prevent duplicate accrual for same attendance
        if frappe.db.exists(
            "Daily Labor Accrual",
            {"attendance": self.name}
        ):
            return

        accrual = frappe.new_doc("Daily Labor Accrual")

        # Header fields
        accrual.accrual_date = self.attendance_date
        accrual.vendor = self.vendor
        accrual.warehouse = self.warehouse
        accrual.attendance = self.name
        accrual.accrual_status = "Posted"

        # Cost summary
        accrual.total_present = self.total_present
        accrual.total_ot_hours = self.total_ot_hours
        accrual.total_cost = self.total_cost

        # Optional: create accrual line (if child table exists)
        if hasattr(accrual, "accrual_lines"):
            accrual.append("accrual_lines", {
                "labor_attendance": self.name,
                "amount": self.total_cost
            })

        accrual.insert(ignore_permissions=True)
        accrual.submit()

    # ------------------------------------------------------------
    # SET VENDOR & WAREHOUSE FROM MDM
    # ------------------------------------------------------------
    def set_vendor_warehouse_from_mdm(self):
        if self.vendor and self.warehouse:
            return

        org = frappe.get_value(
            "MDM Org Header",
            {"is_default": 1},
            ["vendor", "warehouse"],
            as_dict=True
        )

        if org:
            self.vendor = org.vendor
            self.warehouse = org.warehouse

    # ------------------------------------------------------------
    # DUPLICATE ATTENDANCE VALIDATION
    # ------------------------------------------------------------
    def validate_duplicate_attendance(self):
        if not self.labor_allocation or not self.attendance_date:
            return

        existing = frappe.db.exists(
            "Labor Attendance V2",
            {
                "labor_allocation": self.labor_allocation,
                "attendance_date": self.attendance_date,
                "docstatus": 1,
                "name": ["!=", self.name]
            }
        )

        if existing:
            frappe.throw(
                f"Attendance already submitted for Labor Allocation "
                f"{self.labor_allocation} on {self.attendance_date}."
            )

    # ------------------------------------------------------------
    # ATTENDANCE SUMMARY
    # ------------------------------------------------------------
    def calculate_attendance_summary(self):
        total_present = 0
        total_absent = 0
        total_ot_hours = 0
        total_cost = 0

        for row in self.attendance_lines:
            row.present_count = row.present_count or 0
            row.absent_count = row.absent_count or 0
            row.ot_hours = row.ot_hours or 0
            row.rate = row.rate or 0

            normal_cost = row.present_count * row.rate
            ot_cost = row.ot_hours * row.rate
            row.line_cost = normal_cost + ot_cost

            total_present += row.present_count
            total_absent += row.absent_count
            total_ot_hours += row.ot_hours
            total_cost += row.line_cost

        self.total_present = total_present
        self.total_absent = total_absent
        self.total_ot_hours = total_ot_hours
        self.total_cost = total_cost
