import frappe

def execute(filters=None):
    if not filters:
        filters = {}

    columns = [
        {
            "label": "Vendor",
            "fieldname": "vendor",
            "fieldtype": "Link",
            "options": "Labor Vendor",
            "width": 180
        },
        {
            "label": "Warehouse",
            "fieldname": "warehouse",
            "fieldtype": "Link",
            "options": "Warehouse",
            "width": 180
        },
        {
            "label": "Total Present",
            "fieldname": "total_present",
            "fieldtype": "Int",
            "width": 120
        },
        {
            "label": "Total OT Hours",
            "fieldname": "total_ot_hours",
            "fieldtype": "Float",
            "width": 130
        },
        {
            "label": "Total Cost",
            "fieldname": "total_cost",
            "fieldtype": "Currency",
            "width": 140
        },
    ]

    conditions = []
    values = {}

    # Mandatory date filter
    conditions.append("accrual_date BETWEEN %(from_date)s AND %(to_date)s")
    values["from_date"] = filters.get("from_date")
    values["to_date"] = filters.get("to_date")

    if filters.get("vendor"):
        conditions.append("vendor = %(vendor)s")
        values["vendor"] = filters.get("vendor")

    if filters.get("warehouse"):
        conditions.append("warehouse = %(warehouse)s")
        values["warehouse"] = filters.get("warehouse")

    data = frappe.db.sql(
        f"""
        SELECT
            vendor,
            warehouse,
            SUM(total_present) AS total_present,
            SUM(total_ot_hours) AS total_ot_hours,
            SUM(total_cost) AS total_cost
        FROM `tabDaily Labor Accrual`
        WHERE docstatus = 1
          AND {' AND '.join(conditions)}
        GROUP BY vendor, warehouse
        """,
        values,
        as_dict=True
    )

    return columns, data
