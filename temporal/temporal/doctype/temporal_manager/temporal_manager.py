""" Code for DocType 'Temporal Manager' """

# -*- coding: utf-8 -*-
# Copyright (c) 2021, Datahenge LLC and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

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
		""" Create a calendar records in Redis.
		    * Start and End Years will default from the DocType 'Temporal Manager'
			* If no values exist in 'Temporal Manager', there are hard-coded values in temporal.Builder()
		"""
		temporal.Builder.build_all()
		frappe.msgprint(_("Finished rebuilding Redis Calendar."))
