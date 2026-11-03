import frappe

# Instantiate the logger once with your size constraints
vbilog = frappe.logger(
    module="vbint_shared_log", 
    allow_site=True, 
    max_size=1000000,  # 1 MB
    file_count=10
)

vbilog.setLevel("INFO")
