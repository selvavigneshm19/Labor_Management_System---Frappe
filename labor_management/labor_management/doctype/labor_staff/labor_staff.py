# Copyright (c) 2026, FlexiDigit and contributors
# For license information, please see license.txt

# import frappe
import frappe
from frappe.model.document import Document

class LaborStaff(Document):

    def on_submit(self):
        # When approved via workflow
        self.db_set("status", "Active")
