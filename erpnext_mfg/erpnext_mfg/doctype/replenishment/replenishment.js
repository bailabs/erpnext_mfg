// Copyright (c) 2021, Bai Web and Mobile Lab and contributors
// For license information, please see license.txt

frappe.ui.form.on('Replenishment', {
  onload: function (frm) {
    frm.disable_save();
    frm.set_query("warehouse", function () {
      return {
        filters: { "is_group": 0 },
      };
    });
  },
  refresh: function (frm) {
    frm.page.set_primary_action("Update", function () {
      const response = frm.call({
        method: 'update_replenishment_rules',
        doc: frm.doc,
      });
    });
  },
  pull_requested_items_btn: _pull_requested_items,
  warehouse: _load_items,
  supplier: _load_items,
});


frappe.ui.form.on('Replenishment Item', {
  item: function (frm, cdt, cdn) {
    _set_item_qty_details(frm, cdt, cdn);
  },
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


function _pull_requested_items(frm) {
  const d = new frappe.ui.Dialog({
    title: __('Pull Items'),
    fields: [
      {
        label: 'Source',
        fieldname: 'source',
        fieldtype: 'Select',
        options: [
          'Work Order',
          'Bin with Requested Qty',
        ],
        onchange: function () {
          const source = d.get_value('source');
          d.set_df_property('work_order', 'hidden', source !== 'Work Order');
          d.set_df_property('work_order', 'reqd', source === 'Work Order');
        },
      },
      {
        label: 'Work Order',
        fieldname: 'work_order',
        fieldtype: 'Link',
        options: 'Work Order',
        hidden: 1,
      },
    ],
    primary_action: async function (values) {
      if (values.source == 'Work Order') {
        await frm.call({
          method: 'pull_from_work_order',
          doc: frm.doc,
          args: { work_order: values.work_order },
        });
      } else if (values.source == 'Bin with Requested Qty') {
        await frm.call({
          method: 'pull_from_bin',
          doc: frm.doc,
        });
      }
      d.hide();
    }
  });
  d.fields_dict['work_order'].df.get_query = function () {
    return {
      filters: { docstatus: 1 },
    };
  };
  d.show();
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
    freeze: true,
  });
}


async function _get_item_qty_details(item, warehouse) {
  const { message: data } = await frappe.call({
    method: 'erpnext_mfg.api.replenishment.get_item_qty_details',
    args: { item, warehouse },
  });
  return data;
}


async function _set_item_qty_details(frm, cdt, cdn) {
  const child = locals[cdt][cdn];
  const item_qty_details = await _get_item_qty_details(child.item, frm.doc.warehouse);
  if (item_qty_details) {
    frappe.model.set_value(cdt, cdn, "projected_qty", item_qty_details.projected_qty);
    frappe.model.set_value(cdt, cdn, "actual_qty", item_qty_details.actual_qty);
  }
}
