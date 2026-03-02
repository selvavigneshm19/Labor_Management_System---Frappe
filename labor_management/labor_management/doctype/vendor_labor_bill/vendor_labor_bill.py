# Copyright (c) 2026, FlexiDigit and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class VendorLaborBill(Document):

    def validate(self):
        self.validate_accrual_status()
        self.validate_duplicate_billing()
        self.fetch_totals_from_accrual()

    def on_submit(self):
        self.status = "Billed"

    def before_update_after_submit(self):
        frappe.throw("Submitted Vendor Labor Bill cannot be modified")

    def validate_accrual_status(self):
        docstatus = frappe.db.get_value(
            "Monthly Labor Accrual",
            self.monthly_labor_accrual,
            "docstatus"
        )

        if docstatus != 1:
            frappe.throw("Only SUBMITTED Monthly Labor Accrual can be billed")

    def validate_duplicate_billing(self):
        exists = frappe.db.exists(
            "Vendor Labor Bill",
            {
                "monthly_labor_accrual": self.monthly_labor_accrual,
                "docstatus": ["!=", 2]
            }
        )
        if exists and exists != self.name:
            frappe.throw("Vendor Bill already exists for this Monthly Labor Accrual")

    def fetch_totals_from_accrual(self):
        data = frappe.db.get_value(
            "Monthly Labor Accrual",
            self.monthly_labor_accrual,
            [
                "total_present",
                "total_ot_hours",
                "total_cost"
            ],
            as_dict=True
        )

        if data:
            self.total_present = data.total_present
            self.total_ot_hours = data.total_ot_hours
            self.total_cost = data.total_cost
