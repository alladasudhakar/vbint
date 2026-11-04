import frappe
from frappe.model.naming import make_autoname
from frappe.query_builder import DocType
from vbint.vbintlog import vbilog as log


def update_supplier_ids():
   """
      Fetches all supplier records contains alphabets and
      update them with id generation logic
   """

   log.info("\n\n **** update_supplier_ids() called ")
   try:
      Supplier = DocType("Supplier")
      SupGroup = frappe.qb.DocType("Supplier Group")
      query = (
         frappe.qb.from_(Supplier)
         .left_join(SupGroup).on(Supplier.supplier_group == SupGroup.name)
         .select(
            Supplier.name, Supplier.supplier_name,
            Supplier.supplier_group, Supplier.gstin,
            SupGroup.parent_supplier_group
         )
         .where(
            Supplier.supplier_group.isnotnull()
            & Supplier.gstin.isnotnull()
            & Supplier.name.regexp(r"^[a-zA-Z]")
         )
      )
      records = query.run(as_dict=True)
      for rec in records:
         log.info("data " + str(rec))
         gst_prefix = rec.gstin.upper()[:2]
         psg = str(rec.parent_supplier_group.upper())

         sg_prefix = ""
         num_format = ".####"
         if "RAW MATERIAL" in psg:
            sg_prefix = "01"
            num_format = "1.###"
         elif "PACKING MATERIAL" in psg:
            sg_prefix = "02"
            num_format = "2.###"
         elif "SEMI FINISHED" in psg:
            sg_prefix = "03"
            num_format = "4.###"
         elif "FISHISHED PRODUCTS" in psg:
            sg_prefix = "04"
            num_format = "5.###"
         elif "MAINTENANCE & SERVICES" in psg:
            sg_prefix = "05"
            num_format = "3.###"
         elif "CONSUMABLES & SPARES" in psg:
            sg_prefix = "06"
            num_format = "3.###"
         elif "CAPITAL GOODS" in psg:
            sg_prefix = "07"
            num_format = "3.###"
         elif "POP" in psg:
            sg_prefix = "08"
            num_format = "6.###"
         else:
            sg_prefix = "00"
         if not str(rec.name).startswith(gst_prefix):
            naming_series_format = f"{gst_prefix}{sg_prefix}{num_format}"
            newSupName = make_autoname(naming_series_format)
            log.info("update_supplier_id new_name - " +
                     str(newSupName) + " -- rec.name = " + rec.name)
            original_supplier_name = rec.supplier_name
            frappe.enqueue(
               "vbint.vbint.update_supplier_id.execute_suplier_rename",
               doctype="Supplier",
               old_id=rec.name,
               new_id=newSupName,
               original_supplier_name=original_supplier_name,
               enqueue_after_commit=True
            )
      log.info("records = " + str(len(records)))
   except Exception:
      frappe.log_error(title="Error in update_supplier_ids")
      log.info("Error in fetching data")
   log.info("\n update_supplier_ids() completed")


def execute_suplier_rename(doctype, old_id, new_id, original_supplier_name):
   """Executes sequentially inside the background worker thread."""
   log.info(f"execute_suplier_rename() called")
   log.info(
      f"doctype = {doctype} -- old_id = {old_id} --- new_id = {new_id} --- original_supplier_name = {original_supplier_name}")
   try:
      # Step 1: Perform the structural rename across all tables
      frappe.enqueue(
         "frappe.model.rename_doc.rename_doc",
         doctype="Supplier",
         old=old_id,
         new=new_id,
         enqueue_after_commit=True,
         force=True,
         ignore_permissions=True,
         now=True  # Runs synchronously
      )
      log.info(f"step 1 rename completed")
      # Step 2: Now that the rename is 100% complete on this thread,
      # safely restore the original supplier_name field.
      frappe.db.set_value(
         doctype,
         new_id,
         "supplier_name",
         original_supplier_name,
         update_modified=False  # Prevents changing the modified timestamp if undesired
      )
      log.info(f"step 2 original supplier name updated")

      # Step 3: Commit the thread's transaction
      frappe.db.commit()
      log.info(f"step 3 db commit")
   except Exception:
      frappe.log_error(title="Error in update_supplier_ids enqueue rename doc")
      log.info("Error in enqueue rename doc data")
