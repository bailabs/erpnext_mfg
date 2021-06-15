import frappe
from frappe import _


def _get_item_reorder_details(items):
    item_reorders = frappe.get_all(
        "Item Reorder",
        filters={"parent": ("in", items)},
        fields=["parent", "warehouse_reorder_level", "warehouse_reorder_qty"],
    )
    return {x.get("parent"): x for x in item_reorders}


@frappe.whitelist()
def get_item_qty_details(item, warehouse):
    data = frappe.get_all(
        "Bin",
        filters={"item_code": item, "warehouse": warehouse},
        fields=["projected_qty", "actual_qty"],
    )
    if data:
        data = data[0]
        return {
            "projected_qty": data.get("projected_qty"),
            "actual_qty": data.get("actual_qty"),
        }
    return None
