import frappe
from datetime import datetime
from frappe.utils import now_datetime


log = frappe.logger("vbint", allow_site=True)
log.setLevel("DEBUG")


def getDates(dTime: datetime):
   if dTime.month in [1]:
      return (str(dTime.year - 1) + "-12-27 00:00:00",
              str(dTime.year) + "-01-26 23:59:59",
              str(dTime.year) + "-01-27", 31)
   elif dTime.month in [2]:
      return (str(dTime.year) + "-01-27 00:00:00",
              str(dTime.year) + "-02-23 23:59:59",
              str(dTime.year) + "-02-24", 28)
   elif dTime.month in [3]:
      return (str(dTime.year) + "-02-24 00:00:00",
              str(dTime.year) + "-03-26 23:59:59",
              str(dTime.year) + "-03-27", 31)
   elif dTime.month in [4]:
      return (str(dTime.year) + "-03-27 00:00:00",
              str(dTime.year) + "-04-25 23:59:59",
              str(dTime.year) + "-04-26", 30)
   elif dTime.month in [5]:
      return (str(dTime.year) + "-04-26 00:00:00",
              str(dTime.year) + "-05-26 23:59:59",
              str(dTime.year) + "-05-27", 31)
   elif dTime.month in [6]:
      return (str(dTime.year) + "-05-27 00:00:00",
              str(dTime.year) + "-06-25 23:59:59",
              str(dTime.year) + "-06-26", 30)
   elif dTime.month in [7]:
      return (str(dTime.year) + "-06-26 00:00:00",
              str(dTime.year) + "-07-26 23:59:59",
              str(dTime.year) + "-07-27", 31)
   elif dTime.month in [8]:
      return (str(dTime.year) + "-07-27 00:00:00",
              str(dTime.year) + "-08-26 23:59:59",
              str(dTime.year) + "-08-27", 31)
   elif dTime.month in [9]:
      return (str(dTime.year) + "-08-27 00:00:00",
              str(dTime.year) + "-09-25 23:59:59",
              str(dTime.year) + "-09-26", 30)
   elif dTime.month in [10]:
      return (str(dTime.year) + "-09-26 00:00:00",
              str(dTime.year) + "-10-26 23:59:59",
              str(dTime.year) + "-10-27", 31)
   elif dTime.month in [11]:
      return (str(dTime.year) + "-10-27 00:00:00",
              str(dTime.year) + "-11-25 23:59:59",
              str(dTime.year) + "-11-26", 30)
   elif dTime.month in [12]:
      return (str(dTime.year) + "-11-26 00:00:00",
              str(dTime.year) + "-12-26 23:59:59",
              str(dTime.year) + "-12-27", 31)
   return None, None


def submit_monthly_overtime():
   """Fetches all draft overtime requests and submits them."""

   # Optional: If you only want to run this logic on a specific day of the month
   # (e.g., the 25th), you can uncomment the safety check below:
   # if now_datetime().day != 25:
   #     return
   # now_datetime().month

   log.info("\n\n **** submit_monthly_overtime() called " +
            str(now_datetime().month) + " **** \n\n")

   n = 12
   for i in range(1, n + 1):
      dates = getDates(datetime(2026,i,8))
      log.info("testing dates = " + str(dates))

   dates = getDates(now_datetime())
   log.info("fetching overtime records between dates = " +
            dates[0] + " , " + dates[1])
   # Fetch all draft overtime logs
   records = frappe.get_all(
      "Employee Overtime Tool",
      filters=[
         ["ot_date", "between", [dates[0], dates[1]]]
      ],
      # 'items' is the child table fieldname on the Sales Order DocType
      fields=[
         "name",
         "ot_date",
         "employees.employee",
         # "employees.employee_name",
         "employees.othours"
      ]
   )
   log.info("records = " + str(records))
   otMap = {}
   for rec in records:
      otHou = rec.othours
      if rec.employee in otMap:
         otHou += otMap[rec.employee]
      otMap[rec.employee] = otHou
   log.info("otMap = " + str(otMap))
   log.info("payroll_date = " + dates[2])
   log.info("no. of days = " + str(dates[3]))
   for key, value in otMap.items():
      log.info(f"otMap Key: {key} -> otMap Value: {value}")

      exists = frappe.db.exists("Vbond Overtime", {
         "employee": str(key),
         "payroll_date": dates[2]
      })
      log.info("Vbond Overtime Record check = " + str(exists))
      if not exists:
         # Record exists
         log.info(
            "Vbond Overtime Record does not exists, creating Vbond Overtime document")
         doc = frappe.get_doc(
            {
               "doctype": "Vbond Overtime",
               "employee": key,
               "payroll_date": dates[2],
               "working_days": dates[3],
               "overtime_days": round((value / 9), 2)
            }
         )
         doc.insert()
         log.info("Vbond Overtime document created")

   '''
   log.info("creating Vbond Overtime document")
   doc = frappe.get_doc(
      {
         "doctype": "Vbond Overtime",
         "employee": 'VPIPL0007',
         "payroll_date": '2026-08-25',
         "working_days": 30,
         "overtime_days": 1.5
      }
   )
   doc.insert()
   log.info("Vbond Overtime document created")
   '''
   """
   draft_overtime_logs = frappe.get_all(
       "Overtime Request",
       filters={"docstatus": 0, "status": "Draft"},
       fields=["name"]
   )

   for log in draft_overtime_logs:
      try:
         doc = frappe.get_doc("Overtime Request", log.name)
         doc.status = "Submitted"
         doc.submit()  # Changes docstatus to 1
      except Exception as e:
         frappe.log_error(
            f"Failed to submit {log.name}: {str(e)}", "Monthly Overtime Cron Error")
   """
