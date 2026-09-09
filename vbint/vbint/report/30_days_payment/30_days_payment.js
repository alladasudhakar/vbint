// Copyright (c) 2026, sudhakar and contributors
// For license information, please see license.txt

frappe.query_reports["30 Days Payment"] = {
   "filters": [
      {
         "fieldname": "from_date",
         "label": __("From Date"),
         "fieldtype": "Date",
         "default": (function () {
            let today = new Date(frappe.datetime.get_today());
            let year = today.getFullYear();
            // Indian Fiscal year starts on April (Month index 3 in JS)
            // If today is Jan, Feb, or March, the fiscal year started last calendar year.
            if (today.getMonth() < 3) {
               year -= 1;
            }
            return `${year}-04-01`;
         })(),
         "reqd": 1
      },
      {
         "fieldname": "to_date",
         "label": __("To Date"),
         "fieldtype": "Date",
         "default": frappe.datetime.get_today(),
         "reqd": 1
      },
      {
         "fieldname": "customer",
         "label": __("Customer"),
         "fieldtype": "Link",
         "options": "Customer"
      }
   ]
};
