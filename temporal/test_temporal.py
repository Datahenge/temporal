"""

To run these tests:
1.  bench --site <sitename> set-config allow_tests true
2.  bench run-tests --module "temporal.test_temporal"

"""
# Standard Library
import unittest
from datetime import date

# Frappe
import frappe
import frappe.defaults

# Temporal
import temporal


class TestTemporal(unittest.TestCase):
	""" Unit Test for Temporal """
	def setUp(self):
		frappe.flags.test_events_created = True

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_weekday_name(self):
		this_date = date(2021, 4, 17)  # April 17th is a Saturday
		retval = temporal.get_date_metadata(this_date)['weekday_name']
		self.assertTrue(retval == "Saturday")

	def test_weekday_position(self):
		this_date = date(2021, 4, 17)  # April 17th is a Saturday, so should be day number 7.
		retval = temporal.get_date_metadata(this_date)['index_in_week']
		self.assertTrue(retval == 7)

	def test_weeknum_from_date(self):
		this_date = date(2021, 4, 30)  # April 30th 2021 should be week number 18.

		# Test the algorithm used by Internals
		retval = temporal.Internals.date_to_week_tuple(this_date)
		try:
			self.assertTrue(retval[1] == 18)
		except AssertionError as ex:
			print(f"Expected week number 18; found week number {retval} instead.")
			raise ex

		# Test what Redis has stored in its database.
		retval = temporal.get_date_metadata(this_date)['week_number']
		self.assertTrue(retval == 18)

	def test_future_dates_calculator(self):
		# Test a 7 day iteration.
		retval = temporal.calc_future_dates(epoch_date=date(2021, 7, 1),
		                                    multiple_of_days=7,
											earliest_result_date= date(2021, 7, 16),
											qty_of_result_dates=4)
		self.assertTrue(retval == [ date(2021, 7, 22),
		                            date(2021, 7, 29),
		                            date(2021, 8, 5),
			                        date(2021, 8, 12) ])

		# Test a 14 day iteration.
		retval = temporal.calc_future_dates(epoch_date=date(2021, 7, 1),
		                                    multiple_of_days=14,
											earliest_result_date= date(2021, 7, 16),
											qty_of_result_dates=4)
		self.assertTrue(retval == [ date(2021, 7, 29),
		                            date(2021, 8, 12),
		                            date(2021, 8, 26),
			                        date(2021, 9, 9) ])


def custom_test_one(year):
	""" Simple test for printing Dates and Weeks to console.
		bench execute --args "{2021}" temporal.test_temporal.custom_test_one
	"""
	if isinstance(year, str):
		year = int(year)
	start_date = date(year=year, month=1, day=1)
	end_date = date(year=year, month=12, day=31)
	for each_date in temporal.date_range(start_date, end_date):
		week_tuple = temporal.Internals.date_to_week_tuple(each_date)
		print(f"Day {each_date}, Week Year {week_tuple[0]}, Week Number {week_tuple[1]}")

def custom_test_two(any_date_str):
	""" Simple test for printing Dates and Weeks to console.
		bench execute --args "{'2020-12-25'}" temporal.test_temporal.custom_test_two
	"""
	any_date = temporal.datestr_to_date(any_date_str)
	week_tuple = temporal.Internals.date_to_week_tuple(any_date, True)
	print(f"Day {any_date} belongs to Week Year {week_tuple[0]}, Week Number {week_tuple[1]}")
