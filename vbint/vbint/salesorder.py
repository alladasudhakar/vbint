import frappe
from frappe.utils import add_days, today
from frappe import _
from datetime import datetime

log = frappe.logger("vbint", allow_site=True)
log.setLevel("DEBUG")


@frappe.whitelist(allow_guest=False)
def create():
   """
      Whitelisted method to create a Sales Order.
   """
   log.info("salesorder.create()")
   order_data = frappe.request.get_json()
   log.debug("order_data = " + str(order_data))
   if not order_data:
      frappe.throw("Empty or invalid JSON payload received.")
   try:
      # ---------- input data validations ----------
      appOrderId = order_data.get("order_id")
      if appOrderId is None:
         return {
            "status": "failed",
            "error_code": "INVALID_ORDER_ID",
            "error_message": "Order Id missing",
            "failed_field": "order_id"
         }

      orderDate = order_data.get("order_date")
      if orderDate is None:
         return {
            "status": "failed",
            "error_code": "INVALID_ORDER_DATE",
            "error_message": "Order Date is missing",
            "failed_field": "order_date"
         }

      orderStatus = order_data.get("status")
      if orderStatus is None:
         return {
            "status": "failed",
            "error_code": "INVALID_ORDER_STATUS",
            "error_message": "Order Status is missing",
            "failed_field": "status"
         }
      customerName = order_data.get("customer_name")
      log.debug("customerName = " + str(customerName))
      if customerName is None:
         return {
            "status": "failed",
            "app_order_id": appOrderId,
            "error_code": "INVALID_CUSTOMER",
            "error_message": "Customer Name missing",
            "failed_field": "customer_name"
         }
      '''
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
      '''

      # check customer addresses

      addresses = frappe.db.get_list("Address", filters={
         "address_title": ("like", "%" + customerName + "%")
      }, fields=["*"])
      log.debug("addresses = " + str(addresses))
      for add in addresses:
         log.debug(add)
         log.debug(add.address_title)
         log.debug(add.address_line1)
         log.debug(add.address_line2)
      '''
      custAddress = None
      try:
         custAddress = order_data.get("billing_address")
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
      '''
      items = []
      try:
         lineNo = 1
         netWeight = 0
         for item in order_data.get("items", []):
            itemCode = item.get("erp_code")
            itemQty = item.get("quantity")
            itemRate = item.get("rate")
            itemWeight = item.get("weight_kg")
            netWeight += int(int(itemQty) * float(itemWeight))
            if any(v is None for v in [itemCode, itemQty, itemRate, itemWeight]):
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
            items.append(item)
            lineNo += 1
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

      '''
      netWeight = None
      try:
         netWeight = order_data.get("order_total").get("app_total_weight_kg")
      except:
         pass
      if netWeight is None:
         return {
            "status": "failed",
            "app_order_id": appOrderId,
            "error_code": "MISSING_NET_WEIGHT",
            "error_message": "Net weight missing",
            "failed_field": "summary.app_total_weight_kg"
         }
      '''
      total = None
      try:
         total = order_data.get("order_total").get("basic_amount")
      except:
         pass
      if total is None:
         return {
            "status": "failed",
            "app_order_id": appOrderId,
            "error_code": "MISSING_TOTAL",
            "error_message": "total value parameter missing",
            "failed_field": "summary.app_base_price_total"
         }

      taxAmt = order_data.get("order_total").get("taxable_amount")
      log.debug("taxAmt = " + str(taxAmt))
      if taxAmt is None:
         return {
            "status": "failed",
            "app_order_id": appOrderId,
            "error_code": "MISSING_TAXABLE_AMOUNT",
            "error_message": "Taxable Amount parameter missing",
            "failed_field": "order_total.taxable_amount"
         }

      graTotal = order_data.get("order_total").get("grand_total")
      log.debug("graTotal = " + str(graTotal))
      if graTotal is None:
         return {
            "status": "failed",
            "app_order_id": appOrderId,
            "error_code": "MISSING_GRAND_TOTAL",
            "error_message": "Grand Total parameter missing",
            "failed_field": "order_total.grand_total"
         }

      cusDisc = 0
      ppaidDisc = None
      try:
         ppaidDisc = order_data.get("order_total").get("prepaid_discount")
         cusDisc += ppaidDisc
      except:
         pass

      ebirdDisc = None
      try:
         ebirdDisc = order_data.get("order_total").get("early_bird_discount")
         cusDisc += ebirdDisc
      except:
         pass

      log.debug("ppaidDisc = " + str(ppaidDisc))
      log.debug("ebirdDisc = " + str(ebirdDisc))
      log.debug("cusDisc = " + str(cusDisc))

      cusDiscPct = 0
      try:
         cusDiscPct = round(float((cusDisc / graTotal)*100), 2)
      except Exception as ee:
         log.error("cusDiscPct error", exc_info=True)
         #pass
      log.debug("cusDiscPct = " + str(cusDiscPct))

      discBasedOn = order_data.get("discount_based_on")
      log.debug("discBasedOn = " + str(discBasedOn))
      if discBasedOn is None:
         return {
            "status": "failed",
            "app_order_id": appOrderId,
            "error_code": "INVALID_DISCOUNT_BASED_ON",
            "error_message": "Discount Based On parameter missing",
            "failed_field": "discount_based_on"
         }

      traDisc = order_data.get("order_total").get("trade_discount")
      log.debug("traDisc = " + str(traDisc))
      if traDisc is None:
         return {
            "status": "failed",
            "app_order_id": appOrderId,
            "error_code": "INVALID_WEIGHT_VALUE_DISCOUNT",
            "error_message": "Trade Discount parameter missing",
            "failed_field": "order_total.trade_discount"
         }

      wvDiscPct = int((float(traDisc) * 100) / float(total))
      log.debug("wvDiscPct = " + str(wvDiscPct))
      if wvDiscPct is None:
         return {
            "status": "failed",
            "app_order_id": appOrderId,
            "error_code": "INVALID_WEIGHT_VALUE_DISCOUNT",
            "error_message": "Weight Value Discount parameter missing",
            "failed_field": "weight_value_discount_percentage"
         }

      overWrite = order_data.get("custom_allow_overwrite")
      log.debug("overWrite = " + str(overWrite))
      if overWrite is None:
         return {
            "status": "failed",
            "app_order_id": appOrderId,
            "error_code": "INVALID_OVER_WRITE",
            "error_message": "Over Write parameter missing",
            "failed_field": "custom_allow_overwrite"
         }

      # ---------- db validations ----------

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
         "company": "Value Pack India Private Limited",
         "transaction_date": orderDate,
         "status": orderStatus,
         "custom_so_reference_no": appOrderId,
         "delivery_date": add_days(today(), 7),
         "items": [],
         "custom_discount_based_on": discBasedOn,
         "custom_special_discount_percentage": cusDiscPct,
         #"custom_special_discount_amount" : cusDisc,
         "total_net_weight": netWeight,
         "custom_weight_value_discount_percentage": wvDiscPct,
         "custom_allow_overwrite": overWrite,
         "total": total
      }
      log.debug("salesOrdRec = " + str(salesOrdRec))
      sales_order = frappe.get_doc(salesOrdRec)

      # 3. Map and append items to the Sales Order
      for item in items:
         sales_order.append("items", {
            "item_code": item.get("erp_code"),
            "qty": item.get("quantity"),
            "rate": item.get("rate")
         })



      cgstAmt = order_data.get("order_total").get("cgst")
      log.debug("cgstAmt = " + str(cgstAmt))
      if cgstAmt is None:
         return {
            "status": "failed",
            "app_order_id": appOrderId,
            "error_code": "MISSING_CGST",
            "error_message": "CGST parameter missing",
            "failed_field": "order_total.cgst"
         }
      sgstAmt = order_data.get("order_total").get("sgst")
      log.debug("sgstAmt = " + str(sgstAmt))
      if sgstAmt is None:
         return {
            "status": "failed",
            "app_order_id": appOrderId,
            "error_code": "MISSING_SGST",
            "error_message": "SGST parameter missing",
            "failed_field": "order_total.cgst"
         }

      

      log.debug("sgst rec = " + str(taxAmt)+" - "+str(sgstAmt)+" -- "+str(taxAmt+sgstAmt))
      log.debug("cgst rec = " + str(taxAmt)+" - "+str(cgstAmt)+" -- "+str(taxAmt+sgstAmt+cgstAmt))
      '''
         type, account_head, net_amount, tax_amount, total
         Output Tax CGST - VPIPL
      '''

      sales_order.append("taxes", {
            "type": "On Net Total",
            "description": "SGST",
            "account_head": "Output Tax SGST - VPIPL",
            "rate": 9,
            "net_amount": taxAmt,
            "tax_amount": sgstAmt,
            "total": taxAmt+sgstAmt
         })
      sales_order.append("taxes", {
            "type": "On Net Total",
            "description": "CGST",
            "account_head": "Output Tax CGST - VPIPL",
            "rate": 9,
            "net_amount": taxAmt,
            "tax_amount": cgstAmt,
            "total": taxAmt+sgstAmt+cgstAmt
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
