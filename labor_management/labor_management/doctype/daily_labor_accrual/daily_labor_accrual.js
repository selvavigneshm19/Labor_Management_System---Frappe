// Copyright (c) 2026, FlexiDigit and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Daily Labor Accrual", {
// 	refresh(frm) {

// 	},
// });
frappe.ui.form.on('Daily Labor Accrual', {
    attendance(frm) {
        if (frm.doc.attendance) {
            frm.refresh();
        }
    }
});
