import frappe
from frappe.utils import getdate


def process_biometric_logs():
    """
    Process unprocessed biometric punches and create Labor Attendance
    """

    logs = frappe.get_all(
        "Biometric Attendance Log",
        filters={"processed": 0},
        fields=["name", "employee_code", "punch_time", "punch_type"],
        order_by="employee_code, punch_time"
    )

    if not logs:
        return {"status": "no_data"}

    # Group punches by employee + date
    grouped = {}
    for log in logs:
        key = (log.employee_code, getdate(log.punch_time))
        grouped.setdefault(key, []).append(log)

    for (employee_code, attendance_date), punches in grouped.items():
        punches.sort(key=lambda x: x.punch_time)

        check_in = None
        check_out = None

        for p in punches:
            if p.punch_type == "In" and not check_in:
                check_in = p.punch_time
            elif p.punch_type == "Out":
                check_out = p.punch_time

        # No IN punch → skip
        if not check_in:
            continue

        # 🔑 IMPORTANT FIX
        # employee_code === Labor Staff.name
        staff = frappe.db.exists("Labor Staff", employee_code)
        if not staff:
            continue

        # Get active labor allocation
        allocation = frappe.get_value(
            "Vendor Labor Allocation",
            {
                "labor_staff": staff,
                "status": "Active"
            },
            ["name", "warehouse", "vendor"],
            as_dict=True
        )

        if not allocation:
            continue

        # Prevent duplicate attendance
        if frappe.db.exists(
            "Labor Attendance",
            {
                "attendance_date": attendance_date,
                "labor_allocation": allocation.name
            }
        ):
            continue

        # Create Labor Attendance
        attendance = frappe.new_doc("Labor Attendance")
        attendance.attendance_date = attendance_date
        attendance.warehouse = allocation.warehouse
        attendance.vendor = allocation.vendor
        attendance.labor_allocation = allocation.name

        attendance.total_present = 1
        attendance.total_absent = 0
        attendance.total_ot_hours = 0
        attendance.total_cost = 0

        attendance.insert(ignore_permissions=True)

        # Mark biometric logs as processed
        for p in punches:
            frappe.db.set_value(
                "Biometric Attendance Log",
                p.name,
                "processed",
                1
            )

    frappe.db.commit()
    return {"status": "success"}
