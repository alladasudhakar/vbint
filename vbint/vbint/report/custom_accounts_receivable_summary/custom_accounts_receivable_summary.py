# Copyright (c) 2026, sudhakar and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt

# Import the core ERPNext AR Summary execution engine
from .accounts_receivable_summary_filtered import execute as core_execute

log = frappe.logger("vbint", allow_site=True)
log.setLevel("DEBUG")


def execute(filters=None):
   if not filters:
      filters = {}

   log.info("CARS :: filters =  " + str(filters))
   # Initialize an empty cache dictionary
   opening_balance_cache = {}
   customer_meta_cache = {}
   # 1. Fetch columns, data from the native report
   columns, data = core_execute(filters)
   # log.info("CARS :: data = " + str(data))
   filtered_data = []
   if filters.get("start_date"):
      start_date = frappe.utils.getdate(filters.get("start_date"))
      filtered_data = [
         row for row in data
         if frappe.utils.getdate(row.get("posting_date")) >= start_date
      ]
   else:
      filtered_data = data

   territorys = [row.get('territory') for row in filtered_data]
   territoryList = list(dict.fromkeys(territorys))
   print(territoryList)

   outstDict = {}
   for row in filtered_data:
      if isinstance(row, dict):
         if row.get("party"):
            print(str(row))
            # Map territory or fallback to 'Unassigned'
            terr = row.get('territory') or "Unassigned Territory"
            outst_amt = flt(row.get("outstanding", 0))
            # Aggregate by territory
            if terr not in outstDict:
               outstDict[terr] = 0.0
            outstDict[terr] += outst_amt
   print(str(outstDict))
   # unique active customers present in this specific run
   customer_ids = list(set([row.get("party")
                            for row in filtered_data if row.get("party")]))

   if customer_ids:
      # Populate memory caches specifically for these active customers
      opening_balance_cache = build_opening_balance_cache(
         filters, customer_ids)
      customer_meta_cache = build_customer_meta_cache(customer_ids)

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

   columns.insert(9, {
       "fieldname": "opening_balance",
       "label": _("Opening Balance"),
       "fieldtype": "Currency",
       "options": "currency",
       "width": 120
   })

   # 3. Process each customer row to calculate the Open Balance
   for row in filtered_data:
      party = row.get("party")
      if party:
         meta = customer_meta_cache.get(party, {})
         row["opening_balance"] = opening_balance_cache.get(party, 0.0)
         row["customer_address"] = meta.get("address", "")
         row["mobile_no"] = meta.get("mobile_no", "")
         row["gstin"] = meta.get("gstin", "")

   finalData = []
   for key, value in outstDict.items():
      row = {'party': key, 'invoiced': None, 'paid': None,
             'credit_note': None, 'outstanding': value,
             'total_due': None, 'future_amount': None,
             'sales_person': [], 'party_type': 'Territory',
             'range0': None, 'range1': None, 'range2': None, 'range3': None,
             'range4': None, 'range5': None, 'currency': 'INR',
             'territory': '', 'advance': None, 'opening_balance': None}
      finalData.append(row)
   # print(f"{finalData}")
   finalData.extend(filtered_data)
   return columns, finalData


def get_unallocated_advances(customer, company, report_date):
   """Calculates payments received from the customer that are not linked to any invoice."""
   condition = ""
   if report_date:
      condition += " AND posting_date <= %(report_date)s"

   advance = frappe.db.sql(
       f"""
        SELECT SUM(IFNULL(credit, 0) - IFNULL(debit, 0))
        FROM `tabPayment Ledger Entry`
        WHERE company = %(company)s
            AND party_type = 'Customer'
            AND party = %(customer)s
            AND against_voucher_no = voucher_no
            AND delinked = 0
            {condition}
    """,
       {"company": company, "customer": customer, "report_date": report_date},
   )

   return flt(advance[0][0]) if advance and advance[0][0] else 0.0


def build_opening_balance_cache(filters, customer_ids):
   """Fetches historical opening balances only for customers in the report."""
   cacheData = {}
   report_date = filters.get("report_date") or frappe.utils.nowdate()
   company = filters.get("company")

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
         cacheData[entry.party] = flt(entry.opening)
   return cacheData


def build_customer_meta_cache(customer_ids):
   """
   Fetches the primary Address, Phone/Mobile, and GSTIN 
   via an optimized JOIN query strictly for the visible customers.
   """
   cacheData = {}
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

      cacheData[rec.customer] = {
          "address": full_address,
          "mobile_no": mobile,
          "gstin": gstin
      }

   return cacheData
