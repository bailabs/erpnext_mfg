# -*- coding: utf-8 -*-
# Copyright (c) 2021, Bai Web and Mobile Lab and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from erpnext_mfg.api.replenishment import with_qty_details


class Replenishment(Document):
    def on_update(self):
        frappe.db.sql("DELETE FROM tabSingles WHERE doctype = 'Replenishment'")
        frappe.db.sql("DELETE FROM `tabReplenishment Item`")

    def _set_items(self, items):
        for item in items:
            filled_item = with_qty_details(item, self.warehouse)
            self.append("items", filled_item)
        frappe.msgprint(
            _("Please click <strong>Update</strong> in order to save your changes.")
        )

    def _set_order_qty(self):
        for item in self.items:
            item.order_qty = item.max_qty - item.projected_qty

    @frappe.whitelist()
    def load_items(self):
        self.items = []
        self._set_items(_get_replenishment_rules(self.warehouse))

    @frappe.whitelist()
    def pull_from_work_order(self, work_order):
        required_items = _with_item_reorder_details(
            _get_required_items_by_work_order(work_order)
        )
        self._set_items(required_items)
        self._set_order_qty()  # this should be after all the details is set

    @frappe.whitelist()
    def pull_from_bin(self):
        requested_items = _with_item_reorder_details(
            _get_bin_requested_items_by_warehouse(self.warehouse)
        )
        self._set_items(requested_items)
        self._set_order_qty()

    @frappe.whitelist()
    def update_replenishment_rules(self):
        if not self.warehouse:
            frappe.throw(_("Please set your warehouse"))
        _validate_items(self.items)
        _clear_replenishment_rules(self.items, self.warehouse, self.supplier)
        _update_replenishment_rules(self.items, self.warehouse, self.supplier)
        _create_replenishment_rules(self.items, self.warehouse, self.supplier)
        frappe.msgprint(_("Replenishment Rules are updated."))


def _get_replenishment_rules(warehouse):
    return frappe.get_all(
        "Replenishment Rule",
        filters={"warehouse": warehouse},
        fields=[
            "item",
            "min_qty",
            "max_qty",
            "order_qty",
            "supplier",
        ],
    )


def _get_required_items_by_work_order(work_order):
    return frappe.get_all(
        "Work Order Item",
        filters={"parent": work_order},
        fields=["item_code as item", "required_qty as max_qty"],
    )


def _get_bin_requested_items_by_warehouse(warehouse):
    return frappe.db.sql(
        """
        SELECT 
            item_code as item,
            indented_qty as order_qty
        FROM `tabBin`
        WHERE warehouse=%s
        """,
        warehouse,
        as_dict=1,
    )


def _clear_replenishment_rules(items, warehouse, supplier):
    existing_rules = frappe.get_all(
        "Replenishment Rule",
        fields=["name", "item"],
        filters={
            "warehouse": warehouse,
            "supplier": supplier,
        },
    )
    item_names = [x.get("item") for x in items]
    for rule in existing_rules:
        if rule.get("item") not in item_names:
            frappe.delete_doc("Replenishment Rule", rule.get("name"))


def _create_replenishment_rules(items, warehouse, supplier):
    existing_rules = frappe.get_all(
        "Replenishment Rule",
        fields=["item"],
        filters={
            "warehouse": warehouse,
            "supplier": supplier,
        },
    )
    existing_items = [x.get("item") for x in existing_rules]
    for item in items:
        if item.get("item") not in existing_items:
            rule = _get_replenishment_rule(item)
            frappe.get_doc(
                {
                    **rule,
                    "doctype": "Replenishment Rule",
                    "warehouse": warehouse,
                    "supplier": supplier,
                }
            ).insert()


def _update_replenishment_rules(items, warehouse, supplier):
    existing_rules = frappe.get_all(
        "Replenishment Rule",
        fields=["name", "item"],
        filters={
            "warehouse": warehouse,
            "supplier": supplier,
        },
    )
    existing = {x.get("item"): x.get("name") for x in existing_rules}
    item_names = list(existing.keys())
    for item in items:
        name = existing.get(item.get("item"))
        if item.get("item") in item_names and name:
            frappe.db.set_value(
                "Replenishment Rule",
                name,
                _get_replenishment_rule(item),
            )


def _validate_items(items):
    item_names = [x.get("item") for x in items]
    tmp_duplicates = []
    for item in item_names:
        if item not in tmp_duplicates:
            tmp_duplicates.append(item)
        else:
            frappe.throw(
                _(
                    "Unable to update rules. There are item <strong>{}</strong> in multiples.".format(
                        item
                    )
                )
            )

    for item in items:
        if not item.supplier:
            frappe.throw(_("Please set the supplier on Item <strong>{}</strong>".format(item.item)))


def _get_replenishment_rule(item):
    item_dict = item.as_dict()
    unused_keys = [
        "name",
        "owner",
        "creation",
        "modified",
        "modified_by",
        "parent",
        "parentfield",
        "parenttype",
        "idx",
        "docstatus",
        "doctype",
        "__islocal",
        "projected_qty",
        "actual_qty",
        "__unsaved",
    ]
    for x in unused_keys:
        if x in item_dict:
            del item_dict[x]
    return item_dict


def _get_reorder_details(items):
    def make_detail(x):
        return {
            "min_qty": x.get("warehouse_reorder_level"),
            "max_qty": x.get("warehouse_reorder_qty"),
        }

    parent_items = [x.get("item") for x in items]
    reorder_details = frappe.get_all(
        "Item Reorder",
        filters={"parent": ["in", parent_items]},
        fields=["parent", "warehouse_reorder_level", "warehouse_reorder_qty"],
    )
    return {x.get("parent"): make_detail(x) for x in reorder_details}


def _with_item_reorder_details(items):
    reorder_details = _get_reorder_details(items)
    for item in items:
        item_code = item.item
        min_qty = 0
        max_qty = 0
        if item_code in reorder_details:
            min_qty = reorder_details[item_code].get("min_qty")
            max_qty = reorder_details[item_code].get("max_qty")
        item["min_qty"] = min_qty
        item["max_qty"] = max_qty
    return items
