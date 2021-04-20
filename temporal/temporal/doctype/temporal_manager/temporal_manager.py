""" Code for DocType 'Temporal Manager' """

# -*- coding: utf-8 -*-
# Copyright (c) 2021, Datahenge LLC and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document

class TemporalManager(Document):
	""" This DocType just provides a mechanism for displaying buttons on the page. """
	def btn_show_weeks(self):
		frappe.msgprint(_("Call some JS code using frappe.publish_realtime."))
		output = {}
		frappe.publish_realtime("List of Linked Docs", output, user=frappe.session.user)
