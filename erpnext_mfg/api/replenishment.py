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


@frappe.whitelist()
def order_item(item, warehouse, supplier):
    rule = frappe.get_all(
        "Replenishment Rule",
        filters={"item": item, "warehouse": warehouse, "supplier": supplier},
        fields=["order_qty"],
    )
    if not rule:
        frappe.throw(_("Replenishment Rule for Item {} is not found".format(item)))

    rule_data = rule[0]

    po = frappe.new_doc("Purchase Order")
    po.supplier = supplier
    po.set_warehouse = warehouse

    po.append("items", {
        "item_code": item,
        "qty": rule_data.get("order_qty"),
    })

    po.set_missing_values()
    po.schedule_date = po.transaction_date

    po.save()
    po.submit()

    return po.name
