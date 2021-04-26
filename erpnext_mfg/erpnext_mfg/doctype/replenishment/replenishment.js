// Copyright (c) 2021, Bai Web and Mobile Lab and contributors
// For license information, please see license.txt

frappe.ui.form.on('Replenishment', {
	// refresh: function(frm) {

	// }
});


frappe.ui.form.on('Replenishment Item', {
  order_now: function (frm, cdt, cdn) {
    _replenish_item(cdn);
  }
});


async function _replenish_item(name) {
  const response = frappe.call({
    method: 'erpnext_mfg.api.replenishment.replenish_item',
    args: { name },
  });
}
