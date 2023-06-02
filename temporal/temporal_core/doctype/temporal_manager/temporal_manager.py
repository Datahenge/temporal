""" Code for DocType 'Temporal Manager' """

# -*- coding: utf-8 -*-
# Copyright (c) 2023, Datahenge LLC and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import datetime
import pathlib

import frappe
from frappe import _
from frappe.model.document import Document

from temporal import Builder

#
#  Button Naming Convention:  Python functions start with 'button', while DocField names are 'btn'
#

class TemporalManager(Document):
	"""
	This DocType just provides a mechanism for displaying buttons on the page.
	"""

	@frappe.whitelist()
	def button_show_weeks(self):
		frappe.msgprint(_("DEBUG: Calling frappe.publish_realtime.  This should open a dialog, but it does not (known bug 4 June 2021)"))
		frappe.publish_realtime("Dialog Show Redis Weeks", user=frappe.session.user)

	@frappe.whitelist()
	def button_rebuild_calendar_cache(self):
		"""
		Create a calendar records in Redis.
		  * Start and End Years will default from the DocType 'Temporal Manager'
		  * If no values exist in 'Temporal Manager', there are hard-coded values in temporal.Builder()
		"""
		Builder.build_all()
		frappe.msgprint(_("Finished rebuilding Redis Calendar."))

	@frappe.whitelist()
	def button_rebuild_temporal_dates(self):
		"""
		Open the .SQL file in the module, and execute to populate `tabTemporal Dates`
		"""
		print("Rebuilding the Temporal Dates table...")

		this_path = pathlib.Path(__file__)  # path to this Python module
		query_path = this_path.parent / 'rebuild_dates_table.sql'
		if not query_path.exists():
			raise FileNotFoundError(f"Cannot ready query file '{query_path}'")

		frappe.db.sql("TRUNCATE TABLE `tabTemporal Dates`;")

		start_date = datetime.date(int(frappe.db.get_single_value("Temporal Manager", "start_year")), 1, 1)  # January 1st of starting year.
		end_date = datetime.date(int(frappe.db.get_single_value("Temporal Manager", "end_year")), 12, 31)  # December 31st of ending year.


		frappe.db.sql("SET max_recursive_iterations = 20000;")  # IMPORTANT: Overrides the default value of 1000, which limits result to < 3 years.
		with open(query_path, encoding="utf-8") as fstream:
			query = fstream.readlines()
			query = ''.join(query)
			query = query.replace('@StartDate', f"'{start_date}'")
			query = query.replace('@EndDate', f"'{end_date}'")
			frappe.db.sql(query)

		query = """SELECT count(*) FROM `tabTemporal Dates`; """
		row_count = frappe.db.sql(query)
		if row_count:
			row_count = row_count[0][0]
		else:
			row_count = 0
		frappe.db.commit()

		frappe.msgprint("Calculating calendar week numbers...", to_console=True)
		# Next, need to assign Week Numbers.
		temporal_date_keys = frappe.get_list("Temporal Dates", pluck="name", order_by="calendar_date")
		for index, each_key in enumerate(temporal_date_keys):
			try:
				if index % 100 == 0:
					print(f"    Iteration: {index} ...")
				doc_temporal_date = frappe.get_doc("Temporal Dates", each_key)
				doc_temporal_date.set_week_number(raise_on_exception=True)
				doc_temporal_date.save()
				frappe.db.commit()
			except Exception as ex:
				frappe.db.rollback()
				raise ex

		frappe.msgprint(f"Table successfully rebuilt and contains {row_count} rows of calendar dates.")
