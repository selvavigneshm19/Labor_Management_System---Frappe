import frappe
from frappe.model.document import Document
from frappe.utils import today


class WarehouseLaborStructure(Document):
	"""
	Manages approved labor structure per warehouse.
	Ensures vendor allocation matches totals and
	handles versioning logic.
	"""

	def validate(self):
		"""
		Runs BEFORE save.
		Used for data validation and preparation.
		"""
		self.validate_vendor_allocation()
		self.validate_vendor_contracts()
		self.set_version_number()

	def validate_vendor_allocation(self):
		"""
		Business Rule:
		Sum of vendor allocation must match total counts
		"""

		total_skilled_allocated = sum(
			row.skilled_count for row in self.vendor_allocations
		)

		total_semi_allocated = sum(
			row.semi_skilled_count for row in self.vendor_allocations
		)

		total_unskilled_allocated = sum(
			row.unskilled_count for row in self.vendor_allocations
		)

		if total_skilled_allocated != self.total_skilled:
			frappe.throw(
				f"Skilled count mismatch. "
				f"Expected {self.total_skilled}, "
				f"Allocated {total_skilled_allocated}"
			)

		if total_semi_allocated != self.total_semi_skilled:
			frappe.throw(
				f"Semi-skilled count mismatch. "
				f"Expected {self.total_semi_skilled}, "
				f"Allocated {total_semi_allocated}"
			)

		if total_unskilled_allocated != self.total_unskilled:
			frappe.throw(
				f"Unskilled count mismatch. "
				f"Expected {self.total_unskilled}, "
				f"Allocated {total_unskilled_allocated}"
			)

	def validate_vendor_contracts(self):
		"""
		Ensure each vendor has an ACTIVE contract
		for this warehouse and current date
		"""
		today_date = today()

		for row in self.vendor_allocations:
			contract_exists = frappe.db.exists(
				"Vendor Contract",
				{
					"vendor": row.vendor,
					"warehouse": self.warehouse,
					"status": "Active",
					"contract_start_date": ("<=", today_date),
					"contract_end_date": (">=", today_date),
				}
			)

			if not contract_exists:
				frappe.throw(
					f"No active Vendor Contract found for Vendor {row.vendor} "
					f"in Warehouse {self.warehouse}"
				)

	def set_version_number(self):
		"""
		Auto increment version per warehouse
		"""

		if self.is_new():
			prev_version = frappe.db.get_value(
				"Warehouse Labor Structure",
				{"warehouse": self.warehouse},
				"version_number",
				order_by="version_number desc"
			)

			self.version_number = (prev_version or 0) + 1

	def on_submit(self):
		"""
		When approved:
		- Mark previous versions as Superseded
		- Mark current as Active
		"""

		frappe.db.sql("""
			UPDATE `tabWarehouse Labor Structure`
			SET status = 'Superseded'
			WHERE warehouse = %s
			AND name != %s
			AND status = 'Active'
		""", (self.warehouse, self.name))

		self.db_set("status", "Active")
