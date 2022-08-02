# Copyright (c) 2022, Datahenge LLC and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from temporal import TDate

class TemporalDates(Document):

	def set_week_number(self):
		"""
		Set the week number for this Calendar Date.
		"""
		try:
			this_week_number = TDate(self.calendar_date).week_number()
			self.week_number = this_week_number
		except Exception as ex:
			print(ex)
			return

def populate_week_numbers():
	"""
	Mass update, populating the Week Number for every calendar date in the systems.
	"""
	filters = {
		"calendar_date": ["<=", "2025-12-31"],
		"week_number": 0
	}

	date_keys = frappe.get_list("Temporal Dates", filters=filters)
	print(f"Found {len(date_keys)} Temporal Dates that are missing a value for 'week_number'")
	for index, date_key in enumerate(date_keys):
		if index % 500 == 0:
			print(f"Iteration number {index}")
		try:
			doc_temporal_date = frappe.get_doc("Temporal Dates", date_key)
			doc_temporal_date.set_week_number()
			doc_temporal_date.save()
			frappe.db.commit()
		except Exception as ex:
			print(repr(ex))
