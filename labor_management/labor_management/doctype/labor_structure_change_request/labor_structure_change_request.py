# Copyright (c) 2026, FlexiDigit
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today


class LaborStructureChangeRequest(Document):

	def on_update(self):
		# Trigger only when workflow approves
		if self.workflow_state != "Approved":
			return

		# Prevent duplicate creation
		if frappe.db.exists(
			"Warehouse Labor Structure",
			{"change_request": self.name}
		):
			return

		self.create_new_warehouse_labor_structure()

	def create_new_warehouse_labor_structure(self):
		# 1. Get latest ACTIVE submitted structure
		latest = frappe.get_all(
			"Warehouse Labor Structure",
			filters={
				"warehouse": self.warehouse,
				"docstatus": 1,
				"status": "Active"
			},
			fields=["name", "version_number"],
			order_by="version_number desc",
			limit=1
		)

		if not latest:
			frappe.throw("No active Warehouse Labor Structure found")

		latest = latest[0]
		old_doc = frappe.get_doc("Warehouse Labor Structure", latest.name)

		# 2. Create new version (DRAFT)
		new_doc = frappe.new_doc("Warehouse Labor Structure")
		new_doc.warehouse = self.warehouse
		new_doc.effective_date = today()
		new_doc.status = "Draft"
		new_doc.version_number = latest.version_number + 1
		new_doc.display_title = f"{self.warehouse} | V{new_doc.version_number}"
		new_doc.change_reason = self.reason
		new_doc.change_request = self.name

		# 3. Apply proposed values
		new_doc.total_skilled = self.proposed_skilled
		new_doc.total_semi_skilled = self.proposed_semi_skilled
		new_doc.total_unskilled = self.proposed_unskilled

		# 4. Copy vendor allocation
		for row in old_doc.vendor_allocations:
			new_doc.append("vendor_allocations", {
				"vendor": row.vendor,
				"skilled_count": self.proposed_skilled,
				"semi_skilled_count": self.proposed_semi_skilled,
				"unskilled_count": self.proposed_unskilled
			})

		new_doc.insert(ignore_permissions=True)

		frappe.msgprint(
			f"New Warehouse Labor Structure {new_doc.display_title} created as Draft",
			indicator="green"
		)
