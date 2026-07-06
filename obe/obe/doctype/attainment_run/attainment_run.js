frappe.ui.form.on("Attainment Run", {
  refresh(frm) {
    if (frm.is_new()) return;
    frm.add_custom_button("Compute attainment", () => {
      frm.call("compute").then(() => frm.reload_doc());
    }).addClass("btn-primary");
  },
});
