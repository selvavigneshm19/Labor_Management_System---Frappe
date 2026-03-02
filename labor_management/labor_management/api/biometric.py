# import frappe
# from frappe import _

# @frappe.whitelist(allow_guest=True)
# def receive_biometric_punch(data):
#     if not data:
#         frappe.throw(_("No data received from device"))

#     raw_punch_type = (data.get("punch_type") or "").strip().upper()

#     if raw_punch_type == "IN":
#         punch_type = "In"
#     elif raw_punch_type == "OUT":
#         punch_type = "Out"
#     else:
#         frappe.throw(f"Invalid punch_type received: {raw_punch_type}")

#     log = frappe.new_doc("Biometric Attendance Log")
#     log.device_id = data.get("device_id")
#     log.employee_code = data.get("employee_code")
#     log.punch_time = data.get("punch_time")
#     log.punch_type = punch_type   # ✅ normalized value only
#     log.raw_payload = frappe.as_json(data)
#     log.processed = 0

#     log.insert(ignore_permissions=True)
#     frappe.db.commit()

#     return {"status": "success"}





import frappe
from frappe.utils import get_datetime
from labor_management.labor_management.services.attendance_service import process_biometric_log


@frappe.whitelist(allow_guest=True)
def create_punch(device_id=None, employee_code=None, punch_time=None, punch_type=None):

    try:
        # -----------------------------
        # 1️⃣ Basic Validations
        # -----------------------------

        if not employee_code:
            return {
                "status": "error",
                "message": "Employee code missing"
            }

        if not punch_time:
            return {
                "status": "error",
                "message": "Punch time missing"
            }

        if punch_type not in ["In", "Out"]:
            return {
                "status": "error",
                "message": "Invalid punch type"
            }

        # Convert punch_time to proper datetime
        punch_time = get_datetime(punch_time)

        # -----------------------------
        # 2️⃣ Duplicate Check
        # -----------------------------

        existing = frappe.db.exists(
            "Biometric Attendance Log",
            {
                "employee_code": employee_code,
                "punch_time": punch_time,
                "punch_type": punch_type
            }
        )

        if existing:
            return {
                "status": "error",
                "message": "Duplicate punch detected"
            }

        # -----------------------------
        # 3️⃣ Create Biometric Log
        # -----------------------------

        log = frappe.get_doc({
            "doctype": "Biometric Attendance Log",
            "device_id": device_id,
            "employee_code": employee_code,
            "punch_time": punch_time,
            "punch_type": punch_type,
            "processed": 0
        })

        log.insert(ignore_permissions=True)

        # 🔥 IMPORTANT — Commit transaction
        frappe.db.commit()

        # -----------------------------
        # 4️⃣ Process Attendance Logic
        # -----------------------------

        
        log.insert(ignore_permissions=True)
        frappe.db.commit()
        return {
            "status": "success",
            "message": "Punch recorded successfully",
            "log_id": log.name
        }

    except Exception as e:
        frappe.log_error(
            frappe.get_traceback(),
            "Biometric API Error"
        )

        return {
            "status": "error",
            "message": str(e)
        }
