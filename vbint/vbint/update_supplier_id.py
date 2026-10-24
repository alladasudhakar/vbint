import frappe


log = frappe.logger("vbint", allow_site=True)
log.setLevel("DEBUG")


def update_supplier_ids():
   """
      Fetches all supplier records contains alphabets and
      update them with id generation logic
   """

   log.info("\n\n **** update_supplier_ids() called ")

   # Fetch all draft overtime logs
   records = frappe.get_all(
      "Supplier",
      filters={
         "name": ("REGEXP", "^[a-zA-Z]")  # Starts with an English alphabet letter
      },
      # 'items' is the child table fieldname on the Sales Order DocType
      fields=[
         "name",
         "supplier_name",
         "supplier_group"
      ]
   )
   log.info("records = " + str(records))
