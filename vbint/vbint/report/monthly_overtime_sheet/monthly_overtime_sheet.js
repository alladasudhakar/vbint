// Copyright (c) 2026, sudhakar and contributors
// For license information, please see license.txt

frappe.query_reports["Monthly Overtime Sheet"] = {
	filters: [
		{
			fieldname: "filter_based_on",
			label: __("Filter Based On"),
			fieldtype: "Select",
			options: ["Month", "Date Range"],
			default: "Month",
			reqd: 1,
			on_change: (report) => {
				let filter_based_on = frappe.query_report.get_filter_value("filter_based_on");

				if (filter_based_on == "Month") {
					set_reqd_filter("month", true);
					set_reqd_filter("year", true);
					set_reqd_filter("start_date", false);
					set_reqd_filter("end_date", false);
				}
				if (filter_based_on == "Date Range") {
					set_reqd_filter("month", false);
					set_reqd_filter("year", false);
					set_reqd_filter("start_date", true);
					set_reqd_filter("end_date", true);
				}
				report.refresh();
			},
		},
		{
			fieldname: "month",
			label: __("Month"),
			fieldtype: "Select",
			options: [
				{ value: 1, label: __("Apr (27-Mar to 25-Apr)") },
				{ value: 2, label: __("May (26-Apr to 26-May)") },
				{ value: 3, label: __("Jun (27-May to 25-Jun)") },
				{ value: 4, label: __("Jul (26-Jun to 26 Jul)") },
				{ value: 5, label: __("Aug (27-Jul to 26-Aug)") },
				{ value: 6, label: __("Sep (27-Aug to 25-Sep)") },
				{ value: 7, label: __("Oct (26-Sep to 26-Oct)") },
				{ value: 8, label: __("Nov (27-Oct to 25-Nov)") },
				{ value: 9, label: __("Dec (26-Nov to 26 Dec)") },
				{ value: 10, label: __("Jan (27-Dec to 26-Jan)") },
				{ value: 11, label: __("Feb (27-Jan to 23-Feb)") },
				{ value: 12, label: __("Mar (24-Feb to 26-Mar)") },
			],
			default: frappe.datetime.str_to_obj(frappe.datetime.get_today()).getMonth() + 1,
			depends_on: "eval:doc.filter_based_on == 'Month'",
		},
		{
			fieldname: "start_date",
			label: __("Start Date"),
			fieldtype: "Date",
			depends_on: "eval:doc.filter_based_on == 'Date Range'",
			on_change: validate_date_range,
		},
		{
			fieldname: "end_date",
			label: __("End Date"),
			fieldtype: "Date",
			depends_on: "eval:doc.filter_based_on == 'Date Range'",
			on_change: validate_date_range,
		},
		{
			fieldname: "year",
			label: __("Year"),
			fieldtype: "Select",
			depends_on: "eval:doc.filter_based_on == 'Month'",
		},
		{
			fieldname: "employee",
			label: __("Employee"),
			fieldtype: "Link",
			options: "Employee",
			get_query: () => {
				var company = frappe.query_report.get_filter_value("company");
				return {
					filters: {
						company: company,
					},
				};
			},
		},
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
		},
		{
			fieldname: "department",
			label: __("Department"),
			fieldtype: "Link",
			options: "Department",
			get_query: () => {
				var company = frappe.query_report.get_filter_value("company");
				return {
					filters: {
						company: company,
					},
				};
			},
		},
		{
			fieldname: "branch",
			label: __("Branch"),
			fieldtype: "Link",
			options: "Branch",
		},
		{
			fieldname: "group_by",
			label: __("Group By"),
			fieldtype: "Select",
			options: ["", "Branch", "Grade", "Department", "Designation"],
		},
		/*{
			fieldname: "include_company_descendants",
			label: __("Include Company Descendants"),
			fieldtype: "Check",
			default: 1,
		},*/
		{
			fieldname: "summarized_view",
			label: __("Summarized View"),
			fieldtype: "Check",
			default: 0,
		},
	],
	onload: function () {
		frappe.dom.set_style(`
            /* 1. Force the parent block out of normal grid constraints */
            .page-form .report-filter[data-fieldname="month"],
            .page-form .frappe-control[data-fieldname="month"] {
                width: 250px !important;       /* <-- Set your desired width here */
                min-width: 250px !important;   /* Prevents it from crushing */
                max-width: 100% !important;
                flex: 0 0 auto !important;
            }

            /* 2. Strip standard v16 max-width ceilings (which standard jquery .css fails to override) */
            .page-form .frappe-control[data-fieldname="month"] .input-max-width,
            .page-form .frappe-control[data-fieldname="month"] .control-input-wrapper,
            .page-form .frappe-control[data-fieldname="month"] .control-input,
            .page-form .frappe-control[data-fieldname="month"] input,
            .page-form .frappe-control[data-fieldname="month"] select {
                width: 100% !important;
                max-width: 100% !important;
                min-width: 100% !important;
            }
        `);
		frappe.dom.set_style(`
            /* 1. Force the parent block out of normal grid constraints */
            .page-form .report-filter[data-fieldname="company"],
            .page-form .frappe-control[data-fieldname="company"] {
                width: 300px !important;       /* <-- Set your desired width here */
                min-width: 300px !important;   /* Prevents it from crushing */
                max-width: 100% !important;
                flex: 0 0 auto !important;
            }

            /* 2. Strip standard v16 max-width ceilings (which standard jquery .css fails to override) */
            .page-form .frappe-control[data-fieldname="company"] .input-max-width,
            .page-form .frappe-control[data-fieldname="company"] .control-input-wrapper,
            .page-form .frappe-control[data-fieldname="company"] .control-input,
            .page-form .frappe-control[data-fieldname="company"] input,
            .page-form .frappe-control[data-fieldname="company"] select {
                width: 100% !important;
                max-width: 100% !important;
                min-width: 100% !important;
            }
        `);
		return frappe.call({
			method: "hrms.hr.report.monthly_attendance_sheet.monthly_attendance_sheet.get_attendance_years",
			callback: function (r) {
				var year_filter = frappe.query_report.get_filter("year");
				year_filter.df.options = r.message;
				year_filter.df.default = r.message.split("\n")[0];
				year_filter.refresh();
				year_filter.set_input(year_filter.df.default);
			},
		});
	},
	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		const summarized_view = frappe.query_report.get_filter_value("summarized_view");
		const group_by = frappe.query_report.get_filter_value("group_by");

		if (group_by && column.colIndex === 1) {
			value = "<strong>" + value + "</strong>";
		}

		if (!summarized_view) {
			if ((group_by && column.colIndex > 3) || (!group_by && column.colIndex > 2)) {
				if (value == "HD/P") value = "<span style='color:#914EE3'>" + value + "</span>";
				else if (value == "HD/A")
					value = "<span style='color:orange'>" + value + "</span>";
				else if (value == "P" || value == "WFH")
					value = "<span style='color:green'>" + value + "</span>";
				else if (value == "A") value = "<span style='color:red'>" + value + "</span>";
				else if (value == "L") value = "<span style='color:#318AD8'>" + value + "</span>";
				else value = "<span style='color:#878787'>" + value + "</span>";
			}
		}
		else {
			if (column.colIndex == 7){
				value = "<span style='color:blue'>" + value + "</span>";
			}
		}

		return value;
	},
};
function set_reqd_filter(fieldname, is_reqd) {
	let filter = frappe.query_report.get_filter(fieldname);
	filter.df.reqd = is_reqd;
	filter.refresh();
}
function validate_date_range(report) {
	let start_date = frappe.query_report.get_filter_value("start_date");
	let end_date = frappe.query_report.get_filter_value("end_date");
	if (!(start_date && end_date)) return;

	let start = frappe.datetime.str_to_obj(start_date);
	let end = frappe.datetime.str_to_obj(end_date);
	let milli_seconds_in_a_day = 24 * 60 * 60 * 1000;
	let day_diff = Math.floor((end - start) / milli_seconds_in_a_day);
	if (day_diff > 90) {
		frappe.throw({
			message: __("Please set a date range less than 90 days."),
			title: __("Date Range Exceeded"),
		});
	}
	report.refresh();
}
