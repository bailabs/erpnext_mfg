# -*- coding: utf-8 -*-
# Copyright (c) 2021, Bai Web and Mobile Lab and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from erpnext_mfg.api.replenishment import get_item_qty_details


class Replenishment(Document):
    def load_items(self):
        replenishment_rules = _get_replenishment_rules(self.warehouse, self.supplier)
        for data in replenishment_rules:
            data = _with_qty_details(data, self.warehouse)
            self.append("items", data)

    def pull_from_work_order(self, work_order):
        required_items = _get_required_items_by_work_order(work_order)
        for data in required_items:
            data = _with_qty_details(data, self.warehouse)
            self.append("items", data)

    def pull_from_bin(self):
        requested_items = _get_bin_requested_items_by_warehouse(self.warehouse)
        for data in requested_items:
            data = _with_qty_details(data, self.warehouse)
            self.append("items", data)

    def update_replenishment_rules(self):
        if not self.warehouse or not self.supplier:
            frappe.throw(_("Please set your warehouse and/or supplier."))
        _clear_replenishment_rules(self.items, self.warehouse, self.supplier)


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
