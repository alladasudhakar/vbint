import frappe
from frappe.model.naming import make_autoname


log = frappe.logger("vbint", allow_site=True)
log.setLevel("DEBUG")


@frappe.whitelist()
def generate_supplier_id(doc, method):
   # 1. Fallback if no region is selected
   if not doc.custom_region:
      frappe.throw("Please select a Region before saving the Supplier.")
   log.info("generate_supplier_id details - " + str(doc))
   # 2. Clean the region string to use as a prefix (e.g., "North America" -> "NA")
   # Alternatively, store an abbreviation field inside your Region DocType and fetch it here.
   # Takes first 3 letters as an example
   # region_prefix = doc.custom_region.upper()[:3]

   # 3. Define the naming series format: PREFIX-YYYY-.#####
   # Example: APAC-2026-00001
   # naming_series_format = f"{region_prefix}-.YYYY.-.#####"

   # 4. Generate and assign the unique ID using ERPNext's built-in tool
   # doc.name = make_autoname(naming_series_format)


@frappe.whitelist()
def update_supplier_id(doc, method):
   # 1. Skip if this is a brand new document (autoname handles creation)
   if doc.is_new():
      return

   # 2. Fetch the pristine, unaltered document from the database to compare
   db_doc = frappe.get_doc("Supplier", doc.name)
   # 1. Convert the Frappe Document object into a standard Python dictionary
   doc_dict = doc.as_dict()
   log.info("update_supplier_id details - " + str(doc_dict))
   '''
   # Check if the region field was modified during this save action
   if doc.custom_region != db_doc.custom_region:
      if not doc.custom_region:
         frappe.throw("Region cannot be empty. Please select a valid Region.")

      # 3. Generate the new ID format based on the updated region
      region_prefix = doc.custom_region.upper()[:3]
      naming_series_format = f"{region_prefix}-.YYYY.-.#####"
      new_name = make_autoname(naming_series_format)

      # 4. Safely trigger the system-wide database rename
      # Enclose in a try-except block to gracefully handle failures (like duplicate names)
      try:
         old_name = doc.name

         # frappe.rename_doc updates all child/foreign keys and reloads the doc instance
         new_doc_name = frappe.rename_doc(
            "Supplier", old_name, new_name, force=True)

         # Update the current in-memory execution context so ERPNext doesn't look for the old name
         doc.name = new_doc_name

         frappe.msgprint(
            f"Supplier ID successfully updated from {old_name} to {new_doc_name} due to region modification.")

      except Exception as e:
         frappe.log_error(title="Supplier Dynamic Rename Failed",
                          message=frappe.get_traceback())
         frappe.throw(
            f"Could not automatically update Supplier ID code. Error: {str(e)}")
   '''
