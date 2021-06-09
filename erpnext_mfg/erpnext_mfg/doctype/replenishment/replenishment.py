# -*- coding: utf-8 -*-
# Copyright (c) 2021, Bai Web and Mobile Lab and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document


class Replenishment(Document):
    def load_items(self):
        replenishment_rules = _get_replenishment_rules(self.warehouse, self.supplier)
        for data in replenishment_rules:
            self.append("items", data)


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
