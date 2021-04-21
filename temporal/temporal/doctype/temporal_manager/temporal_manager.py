""" Code for DocType 'Temporal Manager' """

# -*- coding: utf-8 -*-
# Copyright (c) 2021, Datahenge LLC and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from datetime import date

import frappe
from frappe import _
from frappe.model.document import Document

import temporal

class TemporalManager(Document):
	""" This DocType just provides a mechanism for displaying buttons on the page. """
	def btn_show_weeks(self):
		frappe.msgprint(_("DEBUG: Calling frappe.publish_realtime.  Dialog should appear next..."))
		frappe.publish_realtime("Dialog Show Redis Weeks", user=frappe.session.user)

	def btn_rebuild_calendar_cache(self):
		# Create a calendar thru current year, instead of Temporal's end date.
		temporal.Builder.build_all(end_year=date.today().year, verbose=True)
		frappe.msgprint(_("Finished rebuilding Redis Calendar."))
