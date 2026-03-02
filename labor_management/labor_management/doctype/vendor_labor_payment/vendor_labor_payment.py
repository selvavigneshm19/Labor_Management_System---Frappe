# Copyright (c) 2026, FlexiDigit and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class VendorLaborPayment(Document):

    def validate(self):
        self.validate_bill_status()

    def on_submit(self):
        # Mark payment as Paid
        self.status = "Paid"

        # Also update linked Vendor Labor Bill payment status
        frappe.db.set_value(
            "Vendor Labor Bill",
            self.vendor_labor_bill,
            "payment_status",
            "Paid"
        )

    def before_update_after_submit(self):
        frappe.throw("Submitted Vendor Labor Payment cannot be modified")

    def validate_bill_status(self):
        bill_status = frappe.db.get_value(
            "Vendor Labor Bill",
            self.vendor_labor_bill,
            "docstatus"
        )

        if bill_status != 1:
            frappe.throw("Only SUBMITTED Vendor Labor Bill can be paid")
