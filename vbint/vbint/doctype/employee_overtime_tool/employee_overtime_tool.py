# Copyright (c) 2026, sudhakar and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname

class EmployeeOvertimeTool(Document):
   def autoname(self):
      # This reads the value set in self.naming_series (e.g., "ATT-TOOL-.YYYY.-")
      # and automatically generates the next sequential number.
      if hasattr(self, "naming_series") and self.naming_series:
         self.name = make_autoname(self.naming_series)
      else:
         # Fallback format if no series is explicitly selected
         self.name = make_autoname("EOT-.YYYY.-.MM.-.###")
