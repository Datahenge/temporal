"""

To run these tests:
1. `bench --site <sitename> set-config allow_tests true`
2. ` bench run-tests --module "temporal.temporal.temporal.test_temporal"`

"""

import frappe
import frappe.defaults
import unittest
from datetime import date

from temporal import temporal

class TestTemporal(unittest.TestCase):
	def setUp(self):
		frappe.flags.test_events_created = True

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_get_calendar_years(self):
		years = { 2020, 2021, 2022}

	def test_weekday_name(self):
		foo = date(2021, 4, 17)  # April 17th is a Saturday
		retval = temporal.date_to_weekday_name(foo)
		self.assertTrue(retval == "Saturday")

	def test_weekday_position(self):
		foo = date(2021, 4, 17)  # April 17th is a Saturday, so should be day number 7.
		retval = temporal.date_to_weekday_position(foo)
		self.assertTrue(retval == 7)
