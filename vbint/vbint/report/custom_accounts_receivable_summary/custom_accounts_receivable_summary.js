// Copyright (c) 2026, sudhakar and contributors
// For license information, please see license.txt

frappe.query_reports["Custom Accounts Receivable Summary"] = {
    // filters: [
    //     ...frappe.query_reports["Accounts Receivable Summary"]?.filters || []
    // ]
    "filters": [
        {
            "fieldname": "company",
            "label": __("Company"),
            "fieldtype": "Link",
            "options": "Company",
            "default": frappe.defaults.get_user_default("Company"),
            "reqd": 1
        },
        {
            "fieldname": "report_date",
            "label": __("Posting Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 1
        },
        {
            fieldname: "party",
            label: __("Party"),
            fieldtype: "MultiSelectList",
            options: "party_type",
            get_data: function (txt) {
                if (!frappe.query_report.filters) return;
                //let party_type = frappe.query_report.get_filter_value("party_type");
                let party_type = "Customer";
                if (!party_type) return;

                return frappe.db.get_link_options(party_type, txt);
            },
        }
    ]
};
