# -*- coding: utf-8 -*-
# Copyright (c) 2021, Bai Web and Mobile Lab and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document


class ReplenishmentRule(Document):
    def validate(self):
        _has_existing_item_rule(self.name, self.item)


def _has_existing_item_rule(name, item):
    rules = frappe.get_all(
        "Replenishment Rule",
        filters={"name": ["!=", name], "item": item},
    )
    if rules:
        frappe.throw(
            _(
                "Unable to create a Replenishment Rule. Please remove existing rule of item {}.".format(
                    item
                )
            )
        )
