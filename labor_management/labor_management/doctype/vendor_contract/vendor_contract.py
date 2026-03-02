# Copyright (c) 2026, FlexiDigit and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class VendorContract(Document):

    def validate(self):
        self.validate_dates()
        self.validate_single_active_contract()

    def validate_dates(self):
        if self.contract_end_date and self.contract_start_date:
            if self.contract_end_date <= self.contract_start_date:
                frappe.throw(
                    "Contract End Date must be after Contract Start Date"
                )

    def validate_single_active_contract(self):
        # Only check when trying to make it Active
        if self.status != "Active":
            return

        existing = frappe.db.exists(
            "Vendor Contract",
            {
                "vendor": self.vendor,
                "warehouse": self.warehouse,
                "status": "Active",
                "name": ["!=", self.name]
            }
        )

        if existing:
            frappe.throw(
                f"An active contract already exists for Vendor {self.vendor} "
                f"in Warehouse {self.warehouse}"
            )

    def on_submit(self):
        # Ensure status is Active on submit
        self.db_set("status", "Active")

    def on_cancel(self):
        # Mark contract as expired on cancel
        self.db_set("status", "Expired")
