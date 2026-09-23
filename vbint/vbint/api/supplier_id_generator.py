import frappe
from frappe.model.naming import make_autoname


log = frappe.logger("vbint", allow_site=True)
log.setLevel("DEBUG")


def generate_supplier_id(doc, method):
   # 1. Fallback if no region is selected
   if not doc.custom_region:
      frappe.throw("Please select a Region before saving the Supplier.")
   log.info("supplier details - " + str(doc))
   # 2. Clean the region string to use as a prefix (e.g., "North America" -> "NA")
   # Alternatively, store an abbreviation field inside your Region DocType and fetch it here.
   # Takes first 3 letters as an example
   # region_prefix = doc.custom_region.upper()[:3]

   # 3. Define the naming series format: PREFIX-YYYY-.#####
   # Example: APAC-2026-00001
   # naming_series_format = f"{region_prefix}-.YYYY.-.#####"

   # 4. Generate and assign the unique ID using ERPNext's built-in tool
   # doc.name = make_autoname(naming_series_format)
