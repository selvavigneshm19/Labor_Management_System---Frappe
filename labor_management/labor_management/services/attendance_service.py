import frappe
from frappe.utils import get_datetime


def process_biometric_log(log_name):

    log = frappe.get_doc("Biometric Attendance Log", log_name)

    if log.processed:
        return

    emp_code = (log.employee_code or "").strip()
    punch_type = log.punch_type
    punch_time = get_datetime(log.punch_time)
    attendance_date = punch_time.date()

    # -----------------------------------
    # Get Active Labor Staff
    # -----------------------------------
    labor_staff = frappe.db.get_value(
        "Labor Staff",
        {"staff_code": emp_code, "status": "Active"},
        ["name", "warehouse", "vendor", "ot_rate"],
        as_dict=True
    )

    if not labor_staff:
        frappe.throw("Active Labor Staff not found")

    # -----------------------------------
    # Get Approved Allocation
    # -----------------------------------
    allocation = frappe.db.get_value(
        "Labor Allocation",
        {
            "allocation_date": attendance_date,
            "warehouse": labor_staff.warehouse,
            "vendor": labor_staff.vendor,
            "docstatus": 1
        },
        "name"
    )

    if not allocation:
        frappe.throw("Approved Allocation not found")

    # ===================================
    # PUNCH IN
    # ===================================
    if punch_type == "In":

        attendance = frappe.get_doc({
            "doctype": "Labor Attendance V2",
            "attendance_date": attendance_date,
            "warehouse": labor_staff.warehouse,
            "vendor": labor_staff.vendor,
            "labor_allocation": allocation,
            "in_time": log.punch_time,
            "source": "Biometric"
        })

        attendance.append("attendance_lines", {
            "labor_staff": labor_staff.name,
            "employee_code": emp_code,
            "present_count": 1,
            "ot_rate": labor_staff.ot_rate or 0
        })

        attendance.insert(ignore_permissions=True)

    # ===================================
    # PUNCH OUT
    # ===================================
    elif punch_type == "Out":

        attendance_name = frappe.db.get_value(
            "Labor Attendance V2",
            {
                "attendance_date": attendance_date,
                "warehouse": labor_staff.warehouse,
                "vendor": labor_staff.vendor,
                "docstatus": 0
            },
            "name",
            order_by="creation desc"
        )

        if not attendance_name:
            frappe.throw("Matching attendance not found")

        attendance = frappe.get_doc("Labor Attendance V2", attendance_name)

        if not attendance.in_time:
            frappe.throw("IN time not found")

        in_time = get_datetime(attendance.in_time)
        worked_hours = (punch_time - in_time).total_seconds() / 3600
        ot_hours = max(worked_hours - 8, 0)

        attendance.out_time = log.punch_time

        for row in attendance.attendance_lines:
            if row.labor_staff == labor_staff.name:
                row.ot_hours = round(ot_hours, 2)
                row.ot_rate = labor_staff.ot_rate or 0
                row.line_cost = round(row.ot_hours * row.ot_rate, 2)

        attendance.save(ignore_permissions=True)
        attendance.submit()

    # -----------------------------------
    # Mark Log Processed
    # -----------------------------------
    log.processed = 1
    log.save(ignore_permissions=True)

    frappe.db.commit()
