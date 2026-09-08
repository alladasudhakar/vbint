# Copyright (c) 2026, sudhakar and contributors
# For license information, please see license.txt

import frappe
from frappe import _
# Import the original report's execute function
from india_compliance.gst_india.report.e_invoice_summary.e_invoice_summary import execute as original_execute


def execute(filters=None):
   # 1. Get the original columns and data
   columns, data = original_execute(filters)

   # 2. Add our new tax columns to the existing columns list
   tax_columns = [
      {
         "label": _("CGST"),
         "fieldname": "cgst",
         "fieldtype": "Currency",
         "width": 120
      },
      {
         "label": _("SGST"),
         "fieldname": "sgst",
         "fieldtype": "Currency",
         "width": 120
      },
      {
         "label": _("IGST"),
         "fieldname": "igst",
         "fieldtype": "Currency",
         "width": 120
      }
   ]
   columns.extend(tax_columns)

   # 3. If there is no data generated, return early
   if not data:
      return columns, data

   print("data = " + str(data))
   # 4. Extract all invoice numbers from the report data to fetch their taxes in bulk
   invoice_names = [row.get("sales_invoice") for row in data if row.get("sales_invoice")]

   invoice_tax_map = {}
   print("invoice_names = " + str(invoice_names))
   if invoice_names:
      # Fetch CGST, SGST, and IGST components directly from the Sales Invoice Item table
      item_data = frappe.db.sql("""
         SELECT 
               parent,
               cgst_amount,
               sgst_amount,
               igst_amount
         FROM 
               `tabSales Invoice Item`
         WHERE 
               parent IN %s
      """, (invoice_names,), as_dict=1)

      # 4. Group and sum up the values per invoice
      for item in item_data:
         parent = item.get("parent")

         if parent not in invoice_tax_map:
            invoice_tax_map[parent] = {"cgst": 0.0, "sgst": 0.0, "igst": 0.0}

         invoice_tax_map[parent]["cgst"] += float(
            item.get("cgst_amount") or 0.0)
         invoice_tax_map[parent]["sgst"] += float(
            item.get("sgst_amount") or 0.0)
         invoice_tax_map[parent]["igst"] += float(
            item.get("igst_amount") or 0.0)
   print("invoice_tax_map = " + str(invoice_tax_map))
   # 5. Inject tax values back into each row of the report data
   for row in data:
      # If it's a dictionary row
      if isinstance(row, dict):
         inv_name = row.get("sales_invoice")
         taxes = invoice_tax_map.get(
            inv_name, {"cgst": 0.0, "sgst": 0.0, "igst": 0.0})
         print("inv_name = " + str(inv_name) + " :: " + str(taxes))
         row["cgst"] = taxes["cgst"]
         row["sgst"] = taxes["sgst"]
         row["igst"] = taxes["igst"]
      # If the standard report returned rows as lists/tuples, convert them to dicts or append elements
      elif isinstance(row, list):
         # It's safer if standard_execute returns a dict. If it returns a list, find the invoice column index.
         pass

   return columns, data
