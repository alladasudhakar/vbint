import frappe
from frappe.utils import add_days, today
from frappe import _
from datetime import datetime

log = frappe.logger("vbint", allow_site=True)
log.setLevel("DEBUG")


@frappe.whitelist(allow_guest=False)
def create(order_data):
   """
      Whitelisted method to create a Sales Order.
      Accepts order_data (dict).
   """
   log.info("salesorder.create()")
   log.debug("order_data = " + str(order_data))
   try:
      # ---------- input data validations ----------
      appOrderId = order_data.get("app_order_id")
      if appOrderId is None:
         return {
            "status": "failed",
            "error_code": "INVALID_APP_ORDER_ID",
            "error_message": "APP Order Id missing",
            "failed_field": "app_order_id"
         }

      '''if not order_data.get("customer_name"):
         frappe.throw(_("Customer Name is required in customer_data"))
         return {
            "status": "failed",
            "error_code": "INVALID_APP_ORDER_ID",
            "error_message": "APP Order Id missing",
            "failed_field": "app_order_id"
         }'''

      companyName = order_data.get("company")
      if companyName is None:
         return {
            "status": "failed",
            "app_order_id": appOrderId,
            "error_code": "INVALID_COMPANY",
            "error_message": "Company Name missing",
            "failed_field": "company"
         }

      customerName = order_data.get("distributor").get("name")
      log.debug("customerName = " + str(customerName))
      if customerName is None:
         return {
            "status": "failed",
            "app_order_id": appOrderId,
            "error_code": "INVALID_CUSTOMER",
            "error_message": "Customer Name missing",
            "failed_field": "distributor.name"
         }

      deliveryDateStr = order_data.get("delivery_date")
      if deliveryDateStr is None:
         return {
            "status": "failed",
            "app_order_id": appOrderId,
            "error_code": "MISSING_DELIVERY_DATE",
            "error_message": "Delivery Date missing",
            "failed_field": "delivery_date"
         }

      deliveryDate = None
      try:
         # Attempt standard parsing
         deliveryDate = datetime.strptime(deliveryDateStr, "%Y-%m-%d")
      except ValueError as e:
         # Fallback or error logging
         log.debug(f"Skipping bad data: '{deliveryDateStr}' (Error: {e})")
         return {
            "status": "failed",
            "app_order_id": appOrderId,
            "error_code": "INVALID_DELIVERY_DATE",
            "error_message": "Delivery Date is invalid",
            "failed_field": "delivery_date"
         }

      custAddress = None
      try:
         custAddress = order_data.get("billing_address").get("address_id")
      except:
         pass
      if custAddress is None:
         return {
            "status": "failed",
            "app_order_id": appOrderId,
            "error_code": "MISSING_CUSTOMER_ADDRESS",
            "error_message": "Customer Address missing",
            "failed_field": "billing_address.address_id"
         }

      shipAddress = None
      try:
         shipAddress = order_data.get("shipping_address").get("address_id")
      except:
         pass
      if shipAddress is None:
         return {
            "status": "failed",
            "app_order_id": appOrderId,
            "error_code": "MISSING_SHIPPING_ADDRESS",
            "error_message": "Shipping Address missing",
            "failed_field": "shipping_address.address_id"
         }
      items = []
      try:
         for item in order_data.get("items", []):
            lineNo = item.get("line_no")
            itemCode = item.get("item_code")
            itemQty = item.get("qty")
            itemRate = item.get("rate")
            if any(v is None for v in [lineNo, itemCode, itemQty, itemRate]):
               return {
                  "status": "failed",
                  "app_order_id": appOrderId,
                  "error_code": "MISSING_ITEM_DETAILS",
                  "error_message": "Item details missing",
                  "failed_field": "items.line_no = " + str(lineNo)
               }
            log.debug("itemCode = " + str(itemCode) + " - itemQty = " + str(itemQty) +
                      " -- itemRate = " + str(itemRate))
            if frappe.db.exists("Item", itemCode):
               log.debug("itemCode = " + str(itemCode) + " exists")
            else:
               return {
                  "status": "failed",
                  "app_order_id": appOrderId,
                  "error_code": "INVALID_ITEM_DETAILS",
                  "error_message": "Item Code does not exists",
                  "failed_field": "items.line_no = " + str(lineNo)
               }
            items.append({
                "item_code": itemCode,
                "qty": itemQty,
                "rate": itemRate
            })
      except:
         pass

      if len(items) == 0:
         return {
            "status": "failed",
            "app_order_id": appOrderId,
            "error_code": "MISSING_ITEM_DETAILS",
            "error_message": "Item details missing",
            "failed_field": "items"
         }

      # ---------- db validations ----------
      if not frappe.db.exists("Company", {"company_name": companyName}):
         return {
            "status": "failed",
            "app_order_id": "11497",
            "error_code": "INVALID_COMPANY",
            "error_message": "Company name not found in ERP",
            "failed_field": "distributor.erp_company"
         }

      ex_customer = frappe.db.exists(
         "Customer", {"customer_name": customerName})

      if ex_customer is None:
         return {
            "status": "failed",
            "app_order_id": "11497",
            "error_code": "INVALID_CUSTOMER",
            "error_message": "Customer doesn't exists",
            "failed_field": "distributor.name"
         }

      if not frappe.db.exists("Customer", {"customer_name": customerName}):
         return {
            "status": "failed",
            "app_order_id": "11497",
            "error_code": "INVALID_CUSTOMER",
            "error_message": "Distributor ID not found in ERP",
            "failed_field": "distributor.name"
         }

      # 2. Create the Sales Order linked to the new Customer
      salesOrdRec = {
         "doctype": "Sales Order",
         "customer": ex_customer,
         "company": order_data.get("company"),
         "transaction_date": today(),
         "custom_so_reference_no": appOrderId,
         "delivery_date": deliveryDate or add_days(today(), 7),
         "items": []
      }
      log.debug("salesOrdRec = " + str(salesOrdRec))
      sales_order = frappe.get_doc(salesOrdRec)

      # 3. Map and append items to the Sales Order
      for item in items:
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
      return {
         "status": "success",
         "message": "Customer and Sales Order created successfully",
         "customer": ex_customer,
         "sales_order": sales_order.name
      }
   except Exception as e:
      # Rollback mutations if anything fails during execution
      frappe.db.rollback()
      log.error("Sales Order Creation Failed", exc_info=True)
      return {
          "status": "failed",
          "error": str(e)
      }
