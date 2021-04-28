import frappe
from frappe import _
from erpnext_mfg.events.replenish_auto_order import get_projected_qty, create_po_from_item


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
                title=_("Unable to create Purchase Order")
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

    replenishment = frappe.get_doc("Replenishment")
    for item in requested_items:
        replenishment.append("items", {
            "item": item.get("item_code"),
            "order_qty": item.get("requested_qty"),
        })

    replenishment.save()

    return replenishment
