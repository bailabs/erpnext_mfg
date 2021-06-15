import frappe
from frappe import _


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
