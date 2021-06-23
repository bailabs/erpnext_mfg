import frappe


def execute():
    frappe.db.sql("DELETE FROM tabSingles WHERE doctype = 'Replenishment'")
    frappe.db.sql("DELETE FROM `tabReplenishment Item`")
