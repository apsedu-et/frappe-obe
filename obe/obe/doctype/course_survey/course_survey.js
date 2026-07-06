frappe.ui.form.on("Course Survey", {
  refresh(frm) {
    if (frm.is_new()) return;
    frm.add_custom_button("Download template", () => {
      frappe.call("obe.api.survey_template", { course: frm.doc.course }).then((r) => {
        frappe.msgprint("<pre>" + frappe.utils.escape_html(r.message) + "</pre>");
      });
    }, "Ratings");
    frm.add_custom_button("Import (paste CSV)", () => {
      const d = new frappe.ui.Dialog({
        title: "Paste survey CSV — roll_no,CO1,CO2,…",
        fields: [{ fieldname: "csv", fieldtype: "Code", label: "CSV", reqd: 1 }],
        primary_action_label: "Import",
        primary_action(v) {
          frappe.call("obe.api.import_survey", { survey: frm.doc.name, csv_text: v.csv }).then((r) => {
            d.hide();
            frappe.show_alert(`Imported ${r.message.rows} ratings`);
            frm.reload_doc();
          });
        },
      });
      d.show();
    }, "Ratings");
  },
});
