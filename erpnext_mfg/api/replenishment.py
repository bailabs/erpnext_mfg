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
    if _is_not_purchase_item(item):
        data = _get_item_boms(item)
    else:
        data = _make_purchase_order(item, warehouse, supplier)
    return {"data": data, "is_bom": True}


def _make_purchase_order(item, warehouse, supplier):
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

    po.append(
        "items",
        {
            "item_code": item,
            "qty": rule_data.get("order_qty"),
        },
    )

    po.set_missing_values()
    po.schedule_date = po.transaction_date

    po.save()

    return po.name


@frappe.whitelist()
def make_work_order(item, bom):
    quantity = frappe.db.get_value("BOM", bom, "quantity")
    work_order = frappe.get_doc(
        {
            "doctype": "Work Order",
            "production_item": item,
            "bom_no": bom,
            "qty": quantity,
        }
    )
    work_order.save()
    return work_order.name


def with_qty_details(data, warehouse):
    item_qty_details = get_item_qty_details(
        data.get("item"),
        warehouse,
    )
    if item_qty_details:
        data = data.update(item_qty_details)
    return data


def _is_not_purchase_item(item):
    purchase_item = frappe.db.get_value("Item", item, "is_purchase_item")
    return not purchase_item


def _get_item_boms(item):
    boms = frappe.get_all(
        "BOM",
        filters={"docstatus": 1, "item": item},
    )
    return [x.get("name") for x in boms]
