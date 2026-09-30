// Copyright (c) 2026, sudhakar and contributors
// For license information, please see license.txt

//Define a global namespace to store your cached employee list
frappe.provide('custom_cache');


frappe.ui.form.on("Employee Overtime Tool", {
   onload: function (frm) {
      // Set date to today only if it's a new document and currently empty
      if (frm.is_new() && !frm.doc.date) {
         frm.set_value('date', frappe.datetime.get_today());
      }
   },

   refresh: function (frm) {
      if (!frm.doc.date) {
         frm.set_value('date', frappe.datetime.get_today());
      }
      fetch_and_cache_employees(frm);

      // Clear default save button since it's a Single DocType acting as a tool
      frm.disable_save();

      // Add a primary custom button on the header
      frm.page.set_primary_action(__('Save'), function () {
         frm.events.save_overtime(frm);
      }, 'tick');

      // Auto-fetch when fields change
      frm.fields_dict['date'].df.change = () => frm.trigger('fetch_and_cache_employees');
      frm.fields_dict['company'].df.change = () => frm.trigger('fetch_and_cache_employees');
      frm.fields_dict['department'].df.change = () => frm.trigger('fetch_and_cache_employees');
   },

   save_overtime: function (frm) {
      if (!frm.doc.date) {
         frappe.msgprint(__('Please select Overtime Date.'));
         return;
      }
      if (!frm.doc.company) {
         frappe.msgprint(__('Please select Company.'));
         return;
      }
      if (!frm.doc.employees || frm.doc.employees.length === 0) {
         frappe.msgprint(__('No employee records available to submit.'));
         return;
      }

      frappe.call({
         method: "vbint.vbint.employee_overtime_tool_api.save_overtime_records",
         args: {
            date: frm.doc.date,
            company: frm.doc.company,
            rows: frm.doc.employees
         },
         freeze: true,
         callback: function (r) {
            if (r.message === "Success") {
               frappe.show_alert({ message: __('Overtime data processed successfully!'), indicator: 'green' });
               frm.trigger('fetch_employees');
            } else {
               frappe.show_alert({ message: __('Error saving Overtime data.'), indicator: 'red' });
               frappe.set_route('List', frm.doctype);
            }
         }
      });
   }
});

// Optional: Automatically fetch the Employee Name when a user manually picks an employee from the dropdown
frappe.ui.form.on('Employee Overtime Tool Item', {

   // Triggers when a row is rendered or opened in form view
   form_render: function (frm, cdt, cdn) {
      set_child_dropdown_query(frm);
   },

   // Triggers when a new row is added
   employees_add: function (frm, cdt, cdn) {
      set_child_dropdown_query(frm);
   },
   // Sync employee metadata elements automatically
   employee: function (frm, cdt, cdn) {
      let row = locals[cdt][cdn];
      if (row.employee) {
         const targetEmployee = custom_cache.employees.find(emp => emp.name === row.employee);
         if (targetEmployee) {
            frappe.model.set_value(cdt, cdn, 'employee_name', targetEmployee.employee_name);
         } else {
            frappe.model.set_value(cdt, cdn, 'employee_name', '');
         }
         /*frappe.db.get_value('Employee', row.employee, 'employee_name', (r) => {
            if (r && r.employee_name) {
               frappe.model.set_value(cdt, cdn, 'employee_name', r.employee_name);
            }
         });*/
      } else {
         frappe.model.set_value(cdt, cdn, 'employee_name', '');
      }
   }
});

// Function to fetch and cache data locally
function fetch_and_cache_employees(frm) {
   //frappe.msgprint(__('fetch_and_cache_employees called()'));
   frappe.call({
      method: "vbint.vbint.employee_overtime_tool_api.get_employees_for_tool", // Route to Python backend method
      args: {
         date: frm.doc.date,
         company: frm.doc.company,
         department: frm.doc.department,
         shift: frm.doc.shift
      },
      callback: function (r) {
         if (r.message) {
            // Cache the clean list of dicts directly in memory
            custom_cache.employees = r.message;
            console.log("r.message = " + JSON.stringify(r.message));
         }
         //frappe.msgprint(__('fetch_and_cache_employees() ' + custom_cache.employees));
      }
   });
}

// Function to handle dropdown queries purely client-side
function set_local_dropdown_query(frm) {
   frappe.msgprint(__('set_local_dropdown_query() '));
   if (frm.fields_dict['employees'] && frm.fields_dict['employees'].grid) {
      let grid_field = frm.fields_dict['employees'].grid.get_field('employee');
      frappe.msgprint(__('set_local_dropdown_query() 22'));
      if (grid_field) {
         // 1. Completely disconnect the default server lookup function
         grid_field.get_query = function () {
            return {
               // Providing a blank method name satisfies Frappe's engine wrapper structure
               query: ""
            };
         };
         frappe.msgprint(__('set_local_dropdown_query() 213 '));
         // 2. Hijack the low-level search routine directly inside the grid control field
         grid_field.search = function (txt) {
            frappe.msgprint(__('set_local_dropdown_query() 216 '));
            let search_term = (txt || "").toLowerCase().trim();
            let filtered_options = [];
            frappe.msgprint(__('set_local_dropdown_query() 218 '));
            if (custom_cache.employees && custom_cache.employees.length) {
               custom_cache.employees.forEach(emp => {
                  let emp_id = String(emp.name || "").trim();
                  let emp_name = String(emp.employee_name || "").trim();

                  if (!search_term || emp_id.toLowerCase().includes(search_term) || emp_name.toLowerCase().includes(search_term)) {
                     // Format: [ value, description ]
                     filtered_options.push([emp_id, emp_name]);
                  }
               });
            }

            // Return a resolved Promise containing the local list array
            // This stops Frappe from generating any Ajax/HTTP server requests!
            frappe.msgprint(__('set_local_dropdown_query() filtered_options = ' + filtered_options));
            return Promise.resolve(filtered_options);
         };
         let filtered_options = [];
         frappe.msgprint(__('set_local_dropdown_query() 249 '));
         if (custom_cache.employees && custom_cache.employees.length) {
            custom_cache.employees.forEach(emp => {
               let emp_id = String(emp.name || "").trim();
               let emp_name = String(emp.employee_name || "").trim();
               // Format: [ value, description ]
               filtered_options.push([emp_id, emp_name]);
            });
         }
         frappe.msgprint(__('set_local_dropdown_query() 261 filtered_options = ' + filtered_options));
         return Promise.resolve(filtered_options);
      } else {
         frappe.msgprint(__('set_local_dropdown_query() 236'));
         return Promise.resolve([]);
      }
   } else {
      frappe.msgprint(__('set_local_dropdown_query() 240'));
      return Promise.resolve([]);
   }
}


// Function to handle dropdown queries from server-side for each row
function set_child_dropdown_query(frm) {
   frm.set_query('employee', 'employees', function (doc, cdt, cdn) {
      return {
         query: 'vbint.vbint.employee_overtime_tool_api.get_employees_for_child_table',
         filters: {
            date: doc.date,
            company: doc.company,
            department: doc.department,
            shift: doc.shift
         }
      };
      /*return {
         query: function (query_doctype, txt, searchfield, start, page_len, options) {

            let live_search = this.txt || txt || "";
            let search_term1 = live_search.toLowerCase().trim();
            console.log('search text1 ' + search_term1);

            let term = txt;
            if (options && options.txt !== undefined) {
               term = options.txt;
            } else if (typeof query_doctype === 'object' && query_doctype.txt !== undefined) {
               // Some versions pass an object as the primary argument
               term = query_doctype.txt;
            }
            let search_term = (term || "").toLowerCase();
            //custom_cache.employees.find(emp => emp.name === row.employee);
            console.log('search text ' + search_term);
            console.log('searchfield ' + searchfield);
            console.log('options ' + options);
            // 3. Filter our local cache object by field values (Company, Dept, and keystroke match)
            let filtered_results = custom_cache.employees.filter(emp => {
               // Match main form constraints if they are filled out
               let match_name = emp.name.toLowerCase().includes(search_term);
               // Match user's typing search term against ID or Name string fields
               let match_emp_name = emp.employee_name.toLowerCase().includes(search_term);
               return match_name;
               //return match_name && match_emp_name;
            });
            console.log("filtered_results = " + filtered_results.length)
            // 4. Map the matching dictionary objects into standard Frappe link response rows
            // Format required: [ [ID, "Help Text Line Item Detail"], ... ]
            let formatted_rows = filtered_results.slice(start, start + page_len).map(emp => {
               console.log(emp);
               let description = `${emp.employee_name} | ${emp.department || "No Dept"} (${emp.designation || "No Title"})`;
               return [emp.name, description];
            });
            console.log("formatted_rows = " + formatted_rows)
            return formatted_rows;
         }
      };*/
   });
}
