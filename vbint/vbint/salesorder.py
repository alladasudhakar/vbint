import frappe
from frappe.utils import add_days, today
from frappe import _


@frappe.whitelist(allow_guest=False)
def create(order_data):
   """
      Whitelisted method to create a Sales Order.
      Accepts order_data (dict).
   """
   print("order_data = " + str(order_data))
   try:
      # 1. Validate mandatory fields
      if not order_data.get("customer_name"):
         frappe.throw(_("Customer Name is required in customer_data"))

      if not order_data.get("company") or not order_data.get("items"):
         frappe.throw(_("Company and Items are required in order_data"))

      # 2. Check if the customer already exists, otherwise create it
      customer_name = order_data.get("customer_name")
      customer_id = ""
      ex_customer = frappe.db.exists("Customer", customer_name)
      print(str(customer_name) + " -1- exists = " + str(ex_customer))
      ex_customer = frappe.db.exists(
         "Customer", {"customer_name": customer_name})
      print(str(customer_name) + " -2- exists = " + str(ex_customer))
      # if not frappe.db.exists("Customer", customer_name): # customer id

      ex_customer = frappe.db.get_value(
         "Customer", {"customer_name": customer_name})
      print(str(customer_name) + " -3- exists = " + str(ex_customer))
      if not frappe.db.exists("Customer", {"customer_name": customer_name}):
         return {
            "status": "failed",
            "app_order_id": "11497",
            "error_code": "INVALID_CUSTOMER",
            "error_message": "Distributor ID not found in ERP",
            "failed_field": "distributor.erp_customer_id"
         }

      # 2. Create the Sales Order linked to the new Customer
      sales_order = frappe.get_doc({
         "doctype": "Sales Order",
         # Uses the dynamic ID generated above
         "customer": customer_id,
         # Must match an exact Company in your system
         "company": order_data.get("company"),
         "transaction_date": today(),
         # Sets delivery deadline to 7 days from now
         "delivery_date": order_data.get("delivery_date") or add_days(today(), 7),
         "items": []
      })

      # 3. Map and append items to the Sales Order
      for item in order_data.get("items", []):
         sales_order.append("items", {
            "item_code": item.get("item_code"),
            "qty": item.get("qty", 1),
            "rate": item.get("rate", 0),
            # Optional: Will fallback to item default if empty
            "warehouse": item.get("warehouse")
         })

      # 3. Save and Submit the Sales Order
      sales_order.insert(ignore_permissions=True)
      # sales_order.submit()  # Finalizes the document and blocks edits

      frappe.db.commit()  # Commits transactions safely
      # return sales_order.name
      return {
         "status": "success",
         "message": "Customer and Sales Order created successfully",
         "customer": customer_id,
         "sales_order": sales_order.name
      }
   except Exception as e:
      # Rollback mutations if anything fails during execution
      frappe.db.rollback()
      frappe.log_error(title="API Order Creation Failed",
                       message=frappe.get_traceback())
      return {
          "status": "failed",
          "error": str(e)
      }
