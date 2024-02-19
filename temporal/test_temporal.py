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

	# All functions must begin with 'test'

	def test_weekday_name(self):
		this_date = date(2021, 4, 17)  # April 17th is a Saturday
		retval = temporal.get_date_metadata(this_date)['weekday_name']
		self.assertTrue(retval == "Saturday")

	def test_weekday_position(self):
		this_date = date(2021, 4, 17)  # April 17th is a Saturday, so should be day number 7.
		retval = temporal.get_date_metadata(this_date)['index_in_week']
		self.assertTrue(retval == 7)

	def test_date_to_weeknums(self):
		expected = [
			{ "calendar_date": "2020-01-01", "week_number": 1 },
			{ "calendar_date": "2020-01-04", "week_number": 1 },
			{ "calendar_date": "2020-01-05", "week_number": 2 },
			{ "calendar_date": "2020-01-11", "week_number": 2 },
			{ "calendar_date": "2020-01-12", "week_number": 3 },
			{ "calendar_date": "2021-01-01", "week_number": 1 },
			{ "calendar_date": "2021-01-02", "week_number": 1 },
			{ "calendar_date": "2021-01-03", "week_number": 2 },
			{ "calendar_date": "2021-01-09", "week_number": 2 },
			{ "calendar_date": "2021-01-10", "week_number": 3 },
			{ "calendar_date": "2021-01-16", "week_number": 3 },
			{ "calendar_date": "2021-04-30", "week_number": 18 },
			{ "calendar_date": "2022-01-01", "week_number": 1 },
			{ "calendar_date": "2022-01-02", "week_number": 2 },
			{ "calendar_date": "2022-01-08", "week_number": 2 },
			{ "calendar_date": "2022-01-09", "week_number": 3 },
			{ "calendar_date": "2022-01-15", "week_number": 3 },
			{ "calendar_date": "2023-01-01", "week_number": 1 },
			{ "calendar_date": "2023-01-07", "week_number": 1 },
			{ "calendar_date": "2023-01-08", "week_number": 2 },
			{ "calendar_date": "2023-01-14", "week_number": 2 },
			{ "calendar_date": "2023-01-15", "week_number": 3 },
		]

		for each in expected:
			calendar_date = temporal.any_to_date(each['calendar_date'])
			calculated_value = temporal.Internals.date_to_week_tuple(calendar_date)[1]
			try:
				self.assertEqual(each['week_number'], calculated_value)
			except AssertionError as ex:
				print(f"Date: {calendar_date}, Expected: {each['week_number']}, Calculated: {calculated_value}")
				calculated_value = temporal.Internals.date_to_week_tuple(calendar_date, verbose=True)[1]
				raise ex

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
	""" 
	Simple test for printing Dates and Weeks to console.

	CLI:	bench execute --args "{'2020-12-25'}" temporal.test_temporal.custom_test_two
	"""
	any_date = temporal.datestr_to_date(any_date_str)
	week_tuple = temporal.Internals.date_to_week_tuple(any_date, True)
	print(f"Day {any_date} belongs to Week Year {week_tuple[0]}, Week Number {week_tuple[1]}")

def test_date_ranges_to_dates():
	"""
	bench execute ftp.test_date_ranges_to_dates
	"""
	from temporal import datestr_to_date

	test_date_ranges = [
		('2023-10-01', '2023-10-05'),
		('2023-11-15', '2023-11-20'),
		('2023-12-09', '2023-12-13')
	]

	expected_dates = [
		datestr_to_date('2023-10-01'), datestr_to_date('2023-10-02'), datestr_to_date('2023-10-03'), datestr_to_date('2023-10-04'), datestr_to_date('2023-10-05'),
		datestr_to_date('2023-11-15'), datestr_to_date('2023-11-16'), datestr_to_date('2023-11-17'), datestr_to_date('2023-11-18'), 
		datestr_to_date('2023-11-19'), datestr_to_date('2023-11-20'),
		datestr_to_date('2023-12-09'), datestr_to_date('2023-12-10'), datestr_to_date('2023-12-11'), datestr_to_date('2023-12-12'), datestr_to_date('2023-12-13')
	]

	actual_dates = temporal.date_ranges_to_dates(test_date_ranges)
	try:
		assert actual_dates == expected_dates
	except AssertionError:
		print("Test failed; expected results do not match actual.")
		print(f"Expected:\n{expected_dates}\n")
		print(f"Actual:\n{actual_dates}")
	else:
		print("\u2713 Successful test of function date_ranges_to_dates()")
