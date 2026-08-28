# Copyright (c) 2026, sudhakar and contributors
# For license information, please see license.txt

import frappe
import time
from frappe import _
from erpnext.accounts.report.accounts_receivable.accounts_receivable import ReceivablePayableReport

log = frappe.logger("vbint", allow_site=True)
log.setLevel("DEBUG")

def execute(filters=None):
    return CustomReceivableReport(filters).run_custom_report()

class CustomReceivableReport(ReceivablePayableReport):
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
        
        # 3. Process opening balances, addresses, and new contact/tax details
        data = self.add_custom_details(data)
        
        # 4. Inject column definitions at specific positions
        

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
        log.info(f"CustomReceivableReport.run() Execution time: {execution_time} seconds")
        return columns, data, chart, report_summary, skip_total_row

    def add_custom_details(self, data):
        report_date = self.filters.get("report_date") or frappe.utils.nowdate()
        company = self.filters.get("company")
        
        # Cache metadata to prevent heavy N+1 query performance degradation
        party_cache = {}
        
        for row in data:
            party = row.get("party") if isinstance(row, dict) else (row[1] if (row and len(row) > 1) else None)
            
            opening_val = 0.0
            address_display = ""
            mobile_no = ""
            gstin = ""
            
            if party:
                # --- Fetch Opening Balance ---
                opening = frappe.db.sql("""
                    SELECT SUM(debit - credit) 
                    FROM `tabGL Entry`
                    WHERE company = %s 
                      AND party_type = 'Customer' 
                      AND party = %s 
                      AND posting_date < %s
                      AND is_cancelled = 0
                """, (company, party, report_date))
                
                opening_val = opening[0][0] if opening and opening[0][0] else 0.0
                
                # --- Fetch Address, Contact Mobile, and GSTIN ---
                if party not in party_cache:
                    # 1. Fetch Primary Address
                    address_data = frappe.db.sql("""
                        SELECT addr.address_line1, addr.address_line2, addr.city
                        FROM `tabAddress` addr
                        JOIN `tabDynamic Link` dl ON dl.parent = addr.name
                        WHERE dl.link_doctype = 'Customer' 
                          AND dl.link_name = %s
                          AND addr.is_primary_address = 1
                        LIMIT 1
                    """, (party,), as_dict=1)
                    
                    if address_data:
                        addr = address_data[0]
                        parts = [addr.get("address_line1"), addr.get("address_line2"), addr.get("city")]
                        address_display = ", ".join([p for p in parts if p])
                    
                    # 2. Fetch Primary Contact Mobile Number
                    contact_data = frappe.db.sql("""
                        SELECT con.mobile_no
                        FROM `tabContact` con
                        JOIN `tabDynamic Link` dl ON dl.parent = con.name
                        WHERE dl.link_doctype = 'Customer' 
                          AND dl.link_name = %s
                          AND con.is_primary_contact = 1
                        LIMIT 1
                    """, (party,), as_dict=1)
                    
                    if contact_data and contact_data[0].get("mobile_no"):
                        mobile_no = contact_data[0].get("mobile_no")
                        
                    # 3. Fetch GSTIN directly from Customer Master
                    customer_gstin = frappe.db.get_value("Customer", party, "gstin")
                    if customer_gstin:
                        gstin = customer_gstin
                        
                    # Save to local execution cache
                    party_cache[party] = {
                        "address": address_display,
                        "mobile": mobile_no,
                        "gstin": gstin
                    }
                else:
                    address_display = party_cache[party]["address"]
                    mobile_no = party_cache[party]["mobile"]
                    gstin = party_cache[party]["gstin"]
            
            # --- Inject Values Based on Row Datatype Layouts ---
            if isinstance(row, dict):
                row["opening_balance"] = opening_val
                row["customer_address"] = address_display
                row["mobile_no"] = mobile_no
                row["gstin"] = gstin
            elif isinstance(row, list):
                row.insert(3, address_display)
                row.insert(4, mobile_no)
                row.insert(5, gstin)
                row.insert(12, opening_val)
                
        return data

'''
    def add_opening_balances(self, data):
        report_date = self.filters.get("report_date") or frappe.utils.nowdate()
        company = self.filters.get("company")
        
        for row in data:
            # Handle dictionary formats or standard arrays
            party = row.get("party") if isinstance(row, dict) else (row[0] if row else None)
            
            if party:
                opening = frappe.db.sql("""
                    SELECT SUM(debit - credit) 
                    FROM `tabGL Entry`
                    WHERE company = %s 
                      AND party_type = 'Customer' 
                      AND party = %s 
                      AND posting_date < %s
                      AND is_cancelled = 0
                """, (company, party, report_date))
                
                opening_val = opening[0][0] if opening and opening[0][0] else 0.0
            else:
                opening_val = 0.0
                
            if isinstance(row, dict):
                row["opening_balance"] = opening_val
            elif isinstance(row, list):
                row.insert(2, opening_val)
                
        return data
'''