frappe.ui.form.on("Assessment", {
  refresh(frm) {
    if (frm.is_new()) return;
    frm.add_custom_button("Download template", () => {
      frappe.call("obe.api.marks_template", { assessment: frm.doc.name }).then((r) => {
        frappe.msgprint("<pre>" + frappe.utils.escape_html(r.message) + "</pre>");
      });
    }, "Marks");
    frm.add_custom_button("Import (paste CSV)", () => {
      const d = new frappe.ui.Dialog({
        title: "Paste marks CSV — roll_no,name,q1,q2,…",
        fields: [{ fieldname: "csv", fieldtype: "Code", label: "CSV", reqd: 1 }],
        primary_action_label: "Import",
        primary_action(v) {
          frappe.call("obe.api.import_marks", { assessment: frm.doc.name, csv_text: v.csv }).then((r) => {
            d.hide();
            frappe.show_alert(`Imported ${r.message.rows} marks`);
            frm.reload_doc();
          });
        },
      });
      d.show();
    }, "Marks");
  },
});
