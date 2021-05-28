import frappe
from frappe import _
from erpnext_mfg.events.replenish_auto_order import (
    get_projected_qty,
    create_po_from_item,
)


@frappe.whitelist()  # erpnext_mfg.api.replenishment.replenish_item
def replenish_item(name):
    replenishment_item = frappe.get_all(
        "Replenishment Item",
        filters={"name": name},
        fields=["item", "order_qty", "max_qty", "supplier"],
    )

    if replenishment_item:
        item = replenishment_item[0]

        warehouse = frappe.db.get_single_value("Replenishment", "warehouse")

        projected_qty = get_projected_qty(item.get("item"), warehouse)
        order_with_projected_qty = projected_qty + item.get("order_qty")

        if item.get("max_qty") >= order_with_projected_qty:
            create_po_from_item(
                item.get("item"),
                item.get("order_qty"),
                warehouse,
                item.get("supplier"),
            )
            frappe.msgprint(_("Successfully created a Purchase Order"))
        else:
            frappe.throw(
                _("Projected Qty + Order Qty would be greater than the Max Qty."),
                title=_("Unable to create Purchase Order"),
            )


@frappe.whitelist()
def show_details(name):
    replenishment_item = frappe.get_all(
        "Replenishment Item",
        filters={"name": name},
        fields=["item", "order_qty", "max_qty", "supplier"],
    )

    if replenishment_item:
        item = replenishment_item[0]
        item_code = item.get("item")
        bin_details = _get_bin_details(item_code)
        frappe.msgprint(
            _get_formatted_bin_details(bin_details),
            title=_("{} Bin Details".format(item_code)),
        )


@frappe.whitelist()  # erpnext_mfg.api.replenishment.pull_requested_items
def pull_requested_items():
    requested_items = frappe.db.sql(
        """
        SELECT 
            item_code,
            SUM(indented_qty) as requested_qty
        FROM `tabBin`
        WHERE indented_qty > 0
        GROUP BY item_code
        """,
        as_dict=1,
    )

    reorder_details = _get_item_reorder_details(
        [x.get("item_code") for x in requested_items]
    )

    replenishment = frappe.get_doc("Replenishment")
    for item in requested_items:
        item_code = item.get("item_code")
        item_reorder = reorder_details.get(item_code, {})
        replenishment.append(
            "items",
            {
                "item": item_code,
                "order_qty": item.get("requested_qty"),
                "min_qty": item_reorder.get("warehouse_reorder_level"),
                "max_qty": item_reorder.get("warehouse_reorder_qty"),
            },
        )

    replenishment.save()

    frappe.msgprint(_("Successfully pulled requested items"))

    return replenishment


def _get_item_reorder_details(items):
    item_reorders = frappe.get_all(
        "Item Reorder",
        filters={"parent": ("in", items)},
        fields=["parent", "warehouse_reorder_level", "warehouse_reorder_qty"],
    )
    return {x.get("parent"): x for x in item_reorders}


def _get_bin_details(item):
    return frappe.get_all(
        "Bin",
        filters={"item_code": item},
        fields=["warehouse", "projected_qty", "actual_qty"],
    )


def _get_formatted_bin_details(bin_details):
    formatted = []
    for x in bin_details:
        formatted.append(
            """
            <div>
                <p><em>{0}</em></p>
                <p>Projected Qty: {1}</p>
                <p>Actual Qty: {2}</p>
            </div>
        """.format(
                x.get("warehouse"),
                x.get("projected_qty"),
                x.get("actual_qty"),
            )
        )
    return "".join(formatted)
