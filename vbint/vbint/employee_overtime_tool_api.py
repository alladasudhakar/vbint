import frappe
import json

log = frappe.logger("vbint", allow_site=True)
log.setLevel("DEBUG")


@frappe.whitelist()
def get_employees_for_tool(date, company, department=None, shift=None):
   filters = {"status": "Active", "company": company}
   if department:
      filters["department"] = department
   if shift:
      filters["default_shift"] = shift
   log.info("get_employees_for_tool() filters = " + str(filters))
   try:
      employees = frappe.get_all(
         "Employee", fields=["name", "employee_name"],
         filters=filters, order_by="employee_name asc"
      )

      for emp in employees:
         # Check if attendance is already tracked for this specific day
         att = frappe.db.get_value("Attendance", {
             "employee": emp.name, "attendance_date": date}, ["name", "status"], as_dict=True)
         if att:
            emp.attendance_id = att.name
            emp.status = att.status
         else:
            emp.attendance_id = None
            emp.status = "Present"  # Customizable system default
   except:
      log.error(msg="err in get employees", stack_info=True)

   return employees


@frappe.whitelist()
def get_employees_for_child_table(doctype, txt, searchfield, start, page_len, filters=None, **kwargs):
   log.info("get_employees_for_child_table() called.")
   log.info("doctype = " + str(doctype) + " ; text = " +
            str(txt) + " ; searchfield = " + str(searchfield))
   cache_key = "vbint:get_employees_for_child_table"

   try:
      # 1. Check if the data exists in cache
      cached_data = frappe.cache().get_value(cache_key)
      if not cached_data:
         # 1. Safely handle the filters argument (Frappe sometimes passes it as a JSON string)
         if isinstance(filters, str):
            try:
               filters = json.loads(filters)
            except ValueError:
               filters = {}
         else:
            filters = filters or {}

         # Extract your parameters
         date = filters.get("date")
         department = filters.get("department")
         company = filters.get("company")
         shift = filters.get("shift")

         filters = {"status": "Active", "company": company}
         if department:
            filters["department"] = department
         if shift:
            filters["default_shift"] = shift

         employees = frappe.get_all(
            "Employee", fields=["name", "employee_name"],
            filters=filters, order_by="employee_name asc"
         )
         log.info("cached_data employees = " + str(employees))
         results = []
         for emp in employees:
            # Check if attendance is already tracked for this specific day
            att = frappe.db.get_value("Attendance", {
                "employee": emp.name, "attendance_date": date}, ["name", "status"], as_dict=True)
            if att:
               emp.attendance_id = att.name
               emp.status = att.status
            else:
               emp.attendance_id = None
               emp.status = "Present"  # Customizable system default
            results.append([emp.name, emp.employee_name])
         frappe.cache().set_value(cache_key, results, expires_in_sec=600)
   except:
      log.error(msg="err in get employees for child", stack_info=True)

   cached_data = frappe.cache().get_value(cache_key)
   log.info("cached_data = " + str(len(str(cached_data))))

   filtered_list = []
   search_str = (txt or "").lower()
   for emp in cached_data:
      # If search text is empty, include everything. Otherwise, look for matches.
      print(str(emp))
      if (not search_str or
         search_str in emp[0].lower() or
         search_str in emp[1].lower()):
         filtered_list.append(emp)
   # return employees
   return filtered_list


@frappe.whitelist()
def save_attendance_records(rows, date, company):
   # Rows are received automatically as strings/dicts depending on submission format
   data = json.loads(rows) if isinstance(rows, str) else rows

   for row in data:
      if row.get("attendance_record"):
         # Update status on existing attendance document entry fields
         frappe.db.set_value(
            "Attendance", row["attendance_record"], "status", row["status"])
      else:
         # Create a brand new submitted system attendance record
         doc = frappe.get_doc(
            {
               "doctype": "Attendance",
               "employee": row["employee"],
               "attendance_date": date,
               "status": row["status"],
               "company": company
            }
         )
         doc.insert()
         doc.submit()

   return "Success"
