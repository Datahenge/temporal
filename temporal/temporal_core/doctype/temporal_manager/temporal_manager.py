""" Code for DocType 'Temporal Manager' """

# -*- coding: utf-8 -*-
# Copyright (c) 2022, Datahenge LLC and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.model.document import Document

#
#  Button Naming Convention:  Python functions start with 'button', while DocField names are 'btn'
#

class TemporalManager(Document):
	""" This DocType just provides a mechanism for displaying buttons on the page. """
	@frappe.whitelist()
	def button_show_weeks(self):
		frappe.msgprint(_("DEBUG: Calling frappe.publish_realtime.  This should open a dialog, but it does not (known bug 4 June 2021)"))
		frappe.publish_realtime("Dialog Show Redis Weeks", user=frappe.session.user)

	@frappe.whitelist()
	def button_rebuild_calendar_cache(self):
		""" Create a calendar records in Redis.
		    * Start and End Years will default from the DocType 'Temporal Manager'
			* If no values exist in 'Temporal Manager', there are hard-coded values in temporal.Builder()
		"""
		from temporal import Builder
		Builder.build_all()
		frappe.msgprint(_("Finished rebuilding Redis Calendar."))

	@frappe.whitelist()
	def button_rebuild_temporal_dates(self):
		"""
			Open the .SQL file in the module, and execute to populate `tabTemporal Dates`
		"""
		# TODO : Button not-yet implemented.  For now you can run the SQL manually.
		frappe.msgprint("Button not-yet implemented.  For now you can run the SQL manually.")

	@frappe.whitelist()
	def button_run_crontab_tests(self):
		from temporal import crontab
		result = crontab.run_tests()
		frappe.msgprint(result)
