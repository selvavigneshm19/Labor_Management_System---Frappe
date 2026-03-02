import frappe
from frappe.model.document import Document
from frappe.utils import getdate


# ----------------------------------------------------
# DOC TYPE CONTROLLER
# ----------------------------------------------------
class DailyLaborAccrual(Document):

    def validate(self):
        self.prevent_duplicate_accrual()

        # IMPORTANT: pull attendance data ONLY for new document
        if self.is_new():
            self.pull_attendance_data()

    def prevent_duplicate_accrual(self):
        if not self.attendance:
            return

        exists = frappe.db.exists(
            "Daily Labor Accrual",
            {
                "attendance": self.attendance,
                "name": ["!=", self.name],
                "docstatus": ["!=", 2]
            }
        )

        if exists:
            frappe.throw(
                f"Daily Labor Accrual already exists for Attendance {self.attendance}"
            )

    def pull_attendance_data(self):
        if not self.attendance:
            return

        # Clear existing lines (safe because only for new doc)
        self.set("accrual_lines", [])

        attendance = frappe.get_doc("Labor Attendance V2", self.attendance)

        total_present = 0
        total_ot_hours = 0
        total_cost = 0

        for row in attendance.attendance_lines:
            line = self.append("accrual_lines", {})
            line.labor_staff = row.labor_staff
            line.in_time = row.in_time
            line.out_time = row.out_time
            line.ot_hours = row.ot_hours or 0
            line.cost = row.cost or 0

            total_present += 1
            total_ot_hours += line.ot_hours
            total_cost += line.cost

        self.total_present = total_present
        self.total_ot_hours = total_ot_hours
        self.total_cost = total_cost


# ----------------------------------------------------
# API / AUTOMATION FUNCTION
# ----------------------------------------------------
@frappe.whitelist()
def generate_daily_labor_accrual(accrual_date):

    accrual_date = getdate(accrual_date)

    attendances = frappe.get_all(
        "Labor Attendance V2",
        filters={
            "attendance_date": accrual_date,
            "docstatus": 1
        },
        pluck="name"
    )

    created = []

    for att in attendances:

        # Skip if already accrued
        if frappe.db.exists(
            "Daily Labor Accrual",
            {"attendance": att, "docstatus": ["!=", 2]}
        ):
            continue

        attendance = frappe.get_doc("Labor Attendance V2", att)

        # SAFETY CHECK (mandatory fields)
        if not attendance.warehouse or not attendance.vendor:
            continue

        accrual = frappe.new_doc("Daily Labor Accrual")
        accrual.accrual_date = accrual_date
        accrual.attendance = att
        accrual.warehouse = attendance.warehouse
        accrual.vendor = attendance.vendor

        accrual.insert(ignore_permissions=True)
        created.append(accrual.name)

    return {
        "status": "success",
        "created_count": len(created),
        "documents": created
    }
