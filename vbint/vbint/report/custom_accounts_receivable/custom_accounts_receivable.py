# Copyright (c) 2026, sudhakar and contributors
# For license information, please see license.txt

import frappe
import time
from frappe import _
from frappe.utils import flt
from erpnext.accounts.report.accounts_receivable.accounts_receivable import ReceivablePayableReport

log = frappe.logger("vbint", allow_site=True)
log.setLevel("DEBUG")


def execute(filters=None):
   return CustomReceivableReport(filters).run_custom_report()


class CustomReceivableReport(ReceivablePayableReport):
   def __init__(self, filters=None):
      super().__init__(filters)
      # Initialize an empty cache dictionary
      self.opening_balance_cache = {}
      self.customer_meta_cache = {}

   def run_custom_report(self):
      log.info("CustomReceivableReport.run()")
      start_time = time.perf_counter()
      # 1. Define base parameters required by ERPNext internal logic
      args = {
          "party_type": "Customer",
          "naming_by": ["Selling Settings", "cust_master_name"],
      }

      # 2. Call parent class run() method and unpack variables
      columns, data, chart, report_summary, skip_total_row, mobile_view_sections = super().run(args)

      # Convert data safely to mutable format
      data = list(data) if data else []

      # unique active customers present in this specific run
      customer_ids = list(set([row.get("party")
                          for row in data if row.get("party")]))

      if customer_ids:
         # Populate memory caches specifically for these active customers
         self.build_opening_balance_cache(customer_ids)
         self.build_customer_meta_cache(customer_ids)

      # 3. Process opening balances, addresses, and new contact/tax details
      # data = self.add_custom_details(data)

      # 4. Inject cached metadata back into your rows via O(1) loop lookups
      for row in data:
         party = row.get("party")
         if party:
            meta = self.customer_meta_cache.get(party, {})
            row["opening_balance"] = self.opening_balance_cache.get(party, 0.0)
            row["customer_address"] = meta.get("address", "")
            row["mobile_no"] = meta.get("mobile_no", "")
            row["gstin"] = meta.get("gstin", "")

      # 5. Inject column definitions at specific positions
      columns.insert(3, {
          "fieldname": "customer_address",
          "label": _("Customer Address"),
          "fieldtype": "Small Text",
          "width": 180
      })

      columns.insert(4, {
          "fieldname": "mobile_no",
          "label": _("Mobile Number"),
          "fieldtype": "Data",
          "width": 130
      })

      columns.insert(5, {
          "fieldname": "gstin",
          "label": _("GSTIN"),
          "fieldtype": "Data",
          "width": 140
      })

      columns.insert(12, {
          "fieldname": "opening_balance",
          "label": _("Opening Balance"),
          "fieldtype": "Currency",
          "options": "currency",
          "width": 120
      })
      end_time = time.perf_counter()
      execution_time = end_time - start_time
      log.info(
         f"CustomReceivableReport.run() Execution time: {execution_time} seconds")
      return columns, data, chart, report_summary, skip_total_row

   def build_opening_balance_cache(self, customer_ids):
      """Fetches historical opening balances only for customers in the report."""
      report_date = self.filters.get("report_date") or frappe.utils.nowdate()
      company = self.filters.get("company")

      if not company or not report_date:
         return

      balances = frappe.db.sql("""
            SELECT party, SUM(debit - credit) as opening
            FROM `tabGL Entry`
            WHERE party_type = 'Customer'
              AND party IN %s
              AND company = %s
              AND posting_date < %s
              AND is_cancelled = 0
            GROUP BY party
        """, (customer_ids, company, report_date), as_dict=True)

      # Populate the local memory cache
      for entry in balances:
         if entry.party:
            self.opening_balance_cache[entry.party] = flt(entry.opening)

   def build_customer_meta_cache(self, customer_ids):
      """
      Fetches the primary Address, Phone/Mobile, and GSTIN 
      via an optimized JOIN query strictly for the visible customers.
      """
      meta_records = frappe.db.sql("""
            SELECT 
                cust.name as customer,
                cust.gstin as c_gstin,
                addr.gstin as a_gstin,
                addr.address_line1,
                addr.address_line2,
                addr.city,
                addr.state,
                addr.pincode,
                addr.phone as address_phone,
                cust.mobile_no as customer_mobile
            FROM `tabCustomer` cust
            LEFT JOIN `tabDynamic Link` dl 
                ON dl.link_name = cust.name 
                AND dl.link_doctype = 'Customer' 
                AND dl.parenttype = 'Address'
            LEFT JOIN `tabAddress` addr 
                ON addr.name = dl.parent 
                AND addr.is_primary_address = 1
            WHERE cust.name IN %s
        """, (customer_ids,), as_dict=True)

      for rec in meta_records:
          # Clean string aggregation for customer address layout
         addr_components = [rec.address_line1,
                            rec.address_line2, rec.city, rec.state, rec.pincode]
         full_address = ", ".join([str(p).strip()
                                  for p in addr_components if p])

         # Process cross-reference fields safely
         mobile = rec.customer_mobile or rec.address_phone or ""
         gstin = rec.c_gstin or rec.a_gstin or ""

         self.customer_meta_cache[rec.customer] = {
             "address": full_address,
             "mobile_no": mobile,
             "gstin": gstin
         }
