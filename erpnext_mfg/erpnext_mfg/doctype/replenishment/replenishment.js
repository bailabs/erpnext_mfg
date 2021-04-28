// Copyright (c) 2021, Bai Web and Mobile Lab and contributors
// For license information, please see license.txt

frappe.ui.form.on('Replenishment', {
  pull_requested_items_btn: _pull_requested_items,
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


async function _pull_requested_items(frm) {
  const response = await frappe.call({
    method: 'erpnext_mfg.api.replenishment.pull_requested_items',
  });
  if (response && response.message) {
    frm.reload_doc();
  }
}
