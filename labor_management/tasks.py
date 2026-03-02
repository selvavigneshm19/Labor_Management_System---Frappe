# import frappe
# from frappe.utils import today

# def expire_vendor_contracts():
# 	"""
# 	Automatically mark Vendor Contracts as Expired
# 	when Contract End Date is less than today
# 	"""

# 	today_date = today()

# 	contracts = frappe.get_all(
# 		"Vendor Contract",
# 		filters={
# 			"status": "Active",
# 			"contract_end_date": ("<", today_date)
# 		},
# 		pluck="name"
# 	)

# 	for contract in contracts:
# 		frappe.db.set_value(
# 			"Vendor Contract",
# 			contract,
# 			"status",
# 			"Expired"
# 		)

# 	if contracts:
# 		frappe.db.commit()




import frappe
from frappe.utils import today, get_first_day, get_last_day, add_months, nowdate


def expire_vendor_contracts():
	"""
	Automatically mark Vendor Contracts as Expired
	when Contract End Date is less than today
	"""
	today_date = today()

	contracts = frappe.get_all(
		"Vendor Contract",
		filters={
			"status": "Active",
			"contract_end_date": ("<", today_date)
		},
		pluck="name"
	)

	for contract in contracts:
		frappe.db.set_value(
			"Vendor Contract",
			contract,
			"status",
			"Expired"
		)

	if contracts:
		frappe.db.commit()


def auto_create_monthly_labor_accrual():
	"""
	Auto create Monthly Labor Accrual for previous month
	"""
	today_date = nowdate()
	prev_month_date = add_months(today_date, -1)

	month_start = get_first_day(prev_month_date)
	month_end = get_last_day(prev_month_date)

	records = frappe.db.sql("""
		SELECT DISTINCT
			vendor,
			warehouse
		FROM `tabDaily Labor Accrual`
		WHERE
			docstatus = 1
			AND accrual_date BETWEEN %s AND %s
	""", (month_start, month_end), as_dict=True)

	for row in records:
		exists = frappe.db.exists(
			"Monthly Labor Accrual",
			{
				"month": month_start,
				"vendor": row.vendor,
				"warehouse": row.warehouse,
				"docstatus": ["!=", 2]
			}
		)
		if exists:
			continue

		doc = frappe.new_doc("Monthly Labor Accrual")
		doc.month = month_start
		doc.vendor = row.vendor
		doc.warehouse = row.warehouse
		doc.status = "Draft"

		doc.insert(ignore_permissions=True)
		doc.submit()

	frappe.db.commit()
