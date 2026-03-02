# Copyright (c) 2026, FlexiDigit and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class MonthlyLaborAccrual(Document):

    def validate(self):
        self.validate_unique_record()
        self.fetch_monthly_totals()

    def on_submit(self):
        self.status = "Posted"

    def validate_unique_record(self):
        exists = frappe.db.exists(
            "Monthly Labor Accrual",
            {
                "month": self.month,
                "vendor": self.vendor,
                "warehouse": self.warehouse,
                "docstatus": ["!=", 2]
            }
        )
        if exists and exists != self.name:
            frappe.throw(
                "Monthly Labor Accrual already exists for this Month, Vendor and Warehouse"
            )

    def fetch_monthly_totals(self):
        data = frappe.db.sql(
            """
            SELECT
                SUM(total_present) AS total_present,
                SUM(total_ot_hours) AS total_ot_hours,
                SUM(total_cost) AS total_cost
            FROM `tabDaily Labor Accrual`
            WHERE
                docstatus = 1
                AND vendor = %s
                AND warehouse = %s
                AND accrual_date BETWEEN
                    DATE_FORMAT(%s, '%%Y-%%m-01')
                    AND LAST_DAY(%s)
            """,
            (self.vendor, self.warehouse, self.month, self.month),
            as_dict=True
        )[0]

        self.total_present = data.total_present or 0
        self.total_ot_hours = data.total_ot_hours or 0
        self.total_cost = data.total_cost or 0

    def before_update_after_submit(self):
        frappe.throw("Posted Monthly Labor Accrual cannot be modified")
