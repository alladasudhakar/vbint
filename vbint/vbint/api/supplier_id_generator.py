import frappe
from frappe.model.naming import make_autoname


log = frappe.logger("vbint", allow_site=True)
log.setLevel("DEBUG")


@frappe.whitelist()
def generate_supplier_id(doc, method):
   # 1. Fallback if no region is selected
   # if not doc.custom_region:
   #   frappe.throw("Please select a Region before saving the Supplier.")
   if not doc.supplier_group:
      frappe.throw("Please select a Supplier Group.")
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

   # 1. Convert the Frappe Document object into a standard Python dictionary
   doc_dict = doc.as_dict()
   log.info("update_supplier_id details - " + str(doc_dict))
   log.info("update_supplier_id gstin - " + str(doc.gstin))
   log.info("update_supplier_id supplier_group - " + str(doc.supplier_group))
   spgSplits = str(doc.supplier_group).split("-")
   if len(spgSplits) > 0:
      log.info("spgSplits[0] - " + spgSplits[0])
   # 2. Determine your intended structural Primary Key ID 
   if doc.gstin is not None and doc.supplier_group is not None:
      gst_prefix = doc.gstin.upper()[:2]
      sg_start = doc.supplier_group.upper()[:2]
      sg_prefix = ""
      if sg_start == "RM":
         sg_prefix = "10"
      elif sg_start == "PM":
         sg_prefix = "20"
      elif sg_start == "FG":
         sg_prefix = "30"
      else:
         sg_prefix = "00"
      naming_series_format = f"{gst_prefix}{sg_prefix}.#####"
      newSupName = make_autoname(naming_series_format)
      log.info("update_supplier_id new_name - " +
               str(newSupName) + " -- doc.name = " + doc.name)
      #3. Preserve the actual Supplier Name exactly as it stands
      original_supplier_name = doc.supplier_name
      original_supplier_name = 'AAGROW TEK COATING PRODUCTS'
      try:
         if doc.name != newSupName:
            # 4. Fire the deferred structural rename against the unique ID
            frappe.enqueue(
               "frappe.model.rename_doc.rename_doc",
               doctype="Supplier",
               old=doc.name,
               new=newSupName,
               enqueue_after_commit=True,  # Delays background queue processing safely
               force=True,                 # Bypasses typical validation blockers
               ignore_permissions=True     # CRITICAL FIX 2: Ignores system user role constraints
            )
            # 3. CRITICAL: Immediately after committing the rename task block, 
            # force-override the supplier_name field back to its original value.
            # This breaks Frappe's default behavior of syncing name -> supplier_name.
            frappe.db.set_value(
                  "Supplier", 
                  newSupName, 
                  "supplier_name", 
                  original_supplier_name
            )
            log.info(f"after frappe.enqueue with parameters")
         return f"Successfully renamed {doc.name} to {newSupName}."

      except Exception as e:
         frappe.log_error(title="Rename Doc Error",
                          message=frappe.get_traceback())
         log.info(f"rename failed.")
         frappe.throw("Failed to rename document.")

