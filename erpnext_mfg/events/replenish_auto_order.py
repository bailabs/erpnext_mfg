import frappe
from frappe import _
from erpnext_mfg.api.replenishment import order_item


# bench execute erpnext_mfg.events.replenish_auto_order.replenish_auto_order
def replenish_auto_order():
    replenishment_items = frappe.get_all(
        "Replenishment Rule",
        filters={"disabled": 0},
        fields=["item", "warehouse", "supplier"],
    )
    for item in replenishment_items:
        order_item(
            item.get("item"),
            item.get("warehouse"),
            item.get("supplier"),
        )
