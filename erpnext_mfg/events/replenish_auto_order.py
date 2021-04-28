import frappe


# bench execute erpnext_mfg.events.replenish_auto_order.replenish_auto_order
def replenish_auto_order():
    replenishment_items = frappe.get_all(
        "Replenishment Item",
        filters={"is_auto_order": 1},
        fields=["item", "order_qty", "max_qty", "supplier"],
    )

    warehouse = frappe.db.get_single_value("Replenishment", "warehouse")
    for item in replenishment_items:
        projected_qty = get_projected_qty(
            item.get("item"),
            warehouse,
        )
        order_with_projected_qty = projected_qty + item.get("order_qty")
        if item.get("max_qty") >= order_with_projected_qty:
            create_po_from_item(
                item.get("item"),
                item.get("order_qty"),
                warehouse,
                item.get("supplier"),
            )


def create_po_from_item(item, qty, warehouse, supplier=None):
    if not supplier:
        supplier = frappe.db.get_single_value("Replenishment", "supplier")

    po = frappe.new_doc("Purchase Order")
    po.supplier = supplier
    po.set_warehouse = warehouse

    po.append("items", {
        "item_code": item,
        "qty": qty
    })

    po.set_missing_values()
    po.schedule_date = po.transaction_date

    po.save()
    po.submit()


def get_projected_qty(item, warehouse):
    bin_detail = frappe.get_all(
        "Bin",
        filters={
            "item_code": item,
            "warehouse": warehouse,
        },
        fields=["projected_qty"]
    )
    return bin_detail[0].get("projected_qty") if bin_detail else None
