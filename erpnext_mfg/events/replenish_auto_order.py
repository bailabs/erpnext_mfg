import frappe
from frappe import _
from erpnext_mfg.api.replenishment import order_item, with_qty_details


# bench execute erpnext_mfg.events.replenish_auto_order.replenish_auto_order
def replenish_auto_order():
    replenishment_items = frappe.get_all(
        "Replenishment Rule",
        filters={"disabled": 0},
        fields=["item", "warehouse", "supplier", "min_qty", "max_qty"],
    )
    for item in replenishment_items:
        filled_item = with_qty_details(item, item.get("warehouse"))
        projected_qty = filled_item.get("projected_qty")
        if projected_qty < filled_item.get(
            "min_qty"
        ) and projected_qty < filled_item.get("max_qty"):
            order_item(
                item.get("item"),
                item.get("warehouse"),
                item.get("supplier"),
            )
