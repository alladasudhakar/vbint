# Copyright (c) 2026, sudhakar and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import today


def execute(filters=None):
   columns = get_columns()
   data = get_data(filters)
   return columns, data


def get_columns():
   return [
      {
         "label": _("Invoice Number"),
         "fieldname": "invoice_id",
         "fieldtype": "Link",
         "options": "Sales Invoice",
         "width": 180
      },
      {
         "label": _("Posting Date"),
         "fieldname": "posting_date",
         "fieldtype": "Date",
         "width": 120
      },
      {
         "label": _("Customer"),
         "fieldname": "customer",
         "fieldtype": "Link",
         "options": "Customer",
         "width": 150
      },
      {
         "label": _("Customer Name"),
         "fieldname": "customer_name",
         "fieldtype": "Data",
         "width": 150
      },
      {
         "label": _("Grand Total"),
         "fieldname": "grand_total",
         "fieldtype": "Currency",
         "options": "currency",
         "width": 120
      },
      {
         "label": _("Outstanding Amount"),
         "fieldname": "outstanding_amount",
         "fieldtype": "Currency",
         "options": "currency",
         "width": 140
      },
      {
         "label": _("Payment Entry"),
         "fieldname": "payment_entry",
         "fieldtype": "Link",
         "options": "Payment Entry",
         "width": 160
      },
      {
         "label": _("Payment Date"),
         "fieldname": "payment_date",
         "fieldtype": "Date",
         "width": 120
      },
      {
         "label": _("Payment Duration (Days)"),
         "fieldname": "payment_duration",
         "fieldtype": "Int",
         "width": 160
      },
      {
         "label": _("Currency"),
         "fieldname": "currency",
         "fieldtype": "Data",
         "hidden": 1
      }
   ]


def get_data(filters):
   # Base query connecting Sales Invoice to Payment Entry References
   query = """
        SELECT 
            si.name AS invoice_id,
            si.posting_date AS posting_date,
            si.customer AS customer,
            si.customer_name AS customer_name,
            si.grand_total AS grand_total,
            si.outstanding_amount AS outstanding_amount,
            si.currency AS currency,
            pe.name AS payment_entry,
            pe.posting_date AS payment_date,
            DATEDIFF(COALESCE(pe.posting_date, %(current_date)s), si.posting_date) AS payment_duration
        FROM 
            `tabSales Invoice` si
        LEFT JOIN 
            `tabPayment Entry Reference` per ON per.reference_name = si.name AND per.reference_doctype = 'Sales Invoice'
        LEFT JOIN 
            `tabPayment Entry` pe ON pe.name = per.parent AND pe.docstatus = 1
        WHERE 
            si.docstatus < 2
            AND si.outstanding_amount <= 0
            AND pe.posting_date IS NOT NULL
            AND DATEDIFF(COALESCE(pe.posting_date, %(current_date)s), si.posting_date) <= 30
    """

   # Inject current date into filters dynamically for the COALESCE function
   filters["current_date"] = today()

   conditions = []
   # Dynamic filters mapping
   if filters.get("from_date") and filters.get("to_date"):
      conditions.append(
         "si.posting_date BETWEEN %(from_date)s AND %(to_date)s")
   if filters.get("customer"):
      conditions.append("si.customer = %(customer)s")

   if conditions:
      query += " AND " + " AND ".join(conditions)

   query += " ORDER BY si.posting_date DESC"

   return frappe.db.sql(query, filters, as_dict=True)
