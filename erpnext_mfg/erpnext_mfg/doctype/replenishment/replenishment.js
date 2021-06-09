// Copyright (c) 2021, Bai Web and Mobile Lab and contributors
// For license information, please see license.txt

frappe.ui.form.on('Replenishment', {
  onload: function (frm) {
    frm.set_query("warehouse", function () {
      return {
        filters: { "is_group": 0 },
      };
    });
  },
  refresh: function (frm) {
    frm.page.set_primary_action("Update", function () {
      frappe.msgprint(__("TODO: implement"));
    });
  },
  pull_requested_items_btn: _pull_requested_items,
  warehouse: _load_items,
  supplier: _load_items,
});


frappe.ui.form.on('Replenishment Item', {
  order_now: function (frm, cdt, cdn) {
    _replenish_item(cdn);
  },
  details: function (frm, cdt, cdn) {
    _show_details(cdn);
  },
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


function _show_details(name) {
  const response = frappe.call({
    method: 'erpnext_mfg.api.replenishment.show_details',
    args: { name },
  });
}


async function _load_items(frm) {
  if (!frm.doc.warehouse || !frm.doc.supplier) {
    return;
  }
  frm.call({
    method: 'load_items',
    doc: frm.doc,
  });
}
