// Copyright (c) 2021, Bai Web and Mobile Lab and contributors
// For license information, please see license.txt

frappe.ui.form.on("Replenishment", {
  onload: function (frm) {
    frm.disable_save();
    frm.set_query("warehouse", function () {
      return {
        filters: { is_group: 0 },
      };
    });
  },
  refresh: function (frm) {
    frm.page.set_primary_action("Update", function () {
      frm.call({
        method: "update_replenishment_rules",
        doc: frm.doc,
        freeze: true,
      });
    });
    frm.set_df_property("warehouse", "reqd", 1);
  },
  pull_requested_items_btn: _pull_requested_items,
  warehouse: _load_items,
});

frappe.ui.form.on("Replenishment Item", {
  item: function (frm, cdt, cdn) {
    _set_item_qty_details(frm, cdt, cdn);
  },
  order_now: function (frm, cdt, cdn) {
    const child = locals[cdt][cdn];
    _order_item(child.item, frm.doc.warehouse, child.supplier);
  },
  details: function (frm, cdt, cdn) {
    _show_details(cdn);
  },
});

function _order_item(item, warehouse, supplier) {
  frappe.confirm(
    "Are you sure you want to order? Don't forget to apply your changes before proceeding.",
    () => {
      frappe.call({
        method: "erpnext_mfg.api.replenishment.order_item",
        args: { item, warehouse, supplier },
        callback: function (r) {
          if (r && r.message) {
            const is_bom = r.message.is_bom;
            if (!is_bom) {
              frappe.msgprint({
                title: __("Order"),
                indicator: "green",
                message: __(
                  `Purchase Order <strong>${r.message}</strong> is created for the Item <em>${item}</em>`
                ),
              });
            } else {
              _make_work_order_dialog(item, r.message.data);
            }
          }
        },
      });
    },
    () => {}
  );
}

function _pull_requested_items(frm) {
  const d = new frappe.ui.Dialog({
    title: __("Pull Items"),
    fields: [
      {
        label: "Source",
        fieldname: "source",
        fieldtype: "Select",
        options: [
          "Work Order",
          "Bin with Requested Qty",
          "By Item Reorder Details",
        ],
        onchange: function () {
          const source = d.get_value("source");
          d.set_df_property("work_order", "hidden", source !== "Work Order");
          d.set_df_property("work_order", "reqd", source === "Work Order");
        },
      },
      {
        label: "Work Order",
        fieldname: "work_order",
        fieldtype: "Link",
        options: "Work Order",
        hidden: 1,
      },
    ],
    primary_action: async function (values) {
      if (values.source == "Work Order") {
        await frm.call({
          method: "pull_from_work_order",
          doc: frm.doc,
          args: { work_order: values.work_order },
        });
      } else if (values.source == "Bin with Requested Qty") {
        await frm.call({
          method: "pull_from_bin",
          doc: frm.doc,
        });
      } else if (values.source == "By Item Reorder Details") {
        await frm.call({
          method: "pull_from_reorder_details",
          doc: frm.doc,
        });
      }
      d.hide();
    },
  });
  d.fields_dict["work_order"].df.get_query = function () {
    return {
      filters: { docstatus: 1 },
    };
  };
  d.show();
}

function _show_details(name) {
  frappe.call({
    method: "erpnext_mfg.api.replenishment.show_details",
    args: { name },
  });
}

async function _load_items(frm) {
  if (!frm.doc.warehouse) {
    return;
  }
  frm.call({
    method: "load_items",
    doc: frm.doc,
    freeze: true,
  });
}

async function _get_item_qty_details(item, warehouse) {
  const { message: data } = await frappe.call({
    method: "erpnext_mfg.api.replenishment.get_item_qty_details",
    args: { item, warehouse },
  });
  return data;
}

async function _set_item_qty_details(frm, cdt, cdn) {
  const child = locals[cdt][cdn];
  const item_qty_details = await _get_item_qty_details(
    child.item,
    frm.doc.warehouse
  );
  if (item_qty_details) {
    frappe.model.set_value(
      cdt,
      cdn,
      "projected_qty",
      item_qty_details.projected_qty
    );
    frappe.model.set_value(cdt, cdn, "actual_qty", item_qty_details.actual_qty);
  }
}

function _make_work_order_dialog(item, boms) {
  frappe.prompt(
    [
      {
        label: "Item",
        fieldname: "item",
        fieldtype: "Link",
        default: item,
        read_only: 1,
      },
      {
        label: "BOM",
        fieldname: "bom",
        fieldtype: "Link",
        options: "BOM",
        get_query: function () {
          return {
            filters: {
              name: ["in", boms],
            },
          };
        },
      },
    ],
    (values) => {
      frappe.call({
        method: "erpnext_mfg.api.replenishment.make_work_order",
        args: {
          item: values.item,
          bom: values.bom,
        },
        callback: function (r) {
          if (r && r.message) {
            frappe.msgprint({
              title: __("Order"),
              indicator: "green",
              message: __(
                `Work Order <strong>${r.message}</strong> is created for the Item <em>${item}</em>`
              ),
            });
          }
        },
      });
    }
  );
}
