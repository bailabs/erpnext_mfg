# -*- coding: utf-8 -*-
# Copyright (c) 2021, Bai Web and Mobile Lab and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from erpnext_mfg.api.replenishment import get_item_qty_details


class Replenishment(Document):
    def _set_items(self, items):
        for item in items:
            filled_item = _with_qty_details(item, self.warehouse)
            self.append("items", filled_item)
        frappe.msgprint(_("Please click <strong>Update</strong> in order to save your changes."))

    def load_items(self):
        self._set_items(_get_replenishment_rules(self.warehouse, self.supplier))

    def pull_from_work_order(self, work_order):
        self._set_items(_get_required_items_by_work_order(work_order))

    def pull_from_bin(self):
        self._set_items(_get_bin_requested_items_by_warehouse(self.warehouse))

    def update_replenishment_rules(self):
        if not self.warehouse or not self.supplier:
            frappe.throw(_("Please set your warehouse and/or supplier."))
        _clear_replenishment_rules(self.items, self.warehouse, self.supplier)
        _update_replenishment_rules(self.items, self.warehouse, self.supplier)
        _create_replenishment_rules(self.items, self.warehouse, self.supplier)
        frappe.msgprint(_("Replenishment Rules are updated."))


def _get_replenishment_rules(warehouse, supplier):
    return frappe.get_all(
        "Replenishment Rule",
        filters={
            "warehouse": warehouse,
            "supplier": supplier,
        },
        fields=[
            "item",
            "min_qty",
            "max_qty",
            "order_qty",
        ],
    )


def _with_qty_details(data, warehouse):
    item_qty_details = get_item_qty_details(
        data.get("item"),
        warehouse,
    )
    if item_qty_details:
        data = data.update(item_qty_details)
    return data


def _get_required_items_by_work_order(work_order):
    return frappe.get_all(
        "Work Order Item",
        filters={"parent": work_order},
        fields=["item_code as item", "required_qty as max_qty"],
    )


def _get_bin_requested_items_by_warehouse(warehouse):
    return frappe.get_all(
        "Bin",
        filters={"warehouse": warehouse},
        fields=["item_code as item", "indented_qty as order_qty"],
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
        "is_auto_order",
    ]
    for x in unused_keys:
        del item_dict[x]
    return item_dict
