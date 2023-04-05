""" temporal.py """

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# Standard Library
import datetime
from datetime import timedelta
from datetime import date as DateType, datetime as datetime_type

# Third Party
import dateutil.parser  # https://stackoverflow.com/questions/48632176/python-dateutil-attributeerror-module-dateutil-has-no-attribute-parse
from dateutil.relativedelta import relativedelta
from dateutil.rrule import SU, MO, TU, WE, TH, FR, SA  # noqa F401

# Temporal Lib
import temporal_lib

from temporal_lib import int_to_ordinal_string as make_ordinal
from temporal_lib.core import (
	localize_datetime,
	calc_future_dates,
	date_generator_type_1,
	date_is_between, date_range,
	date_range_from_strdates,
	get_earliest_date,
	get_latest_date
)
from temporal_lib.tlib_types import (
	any_to_iso_date_string,
	any_to_date,
	any_to_datetime,
	any_to_time,
	datestr_to_date,
	date_to_iso_string,
	date_to_datetime_midnight,
	datetime_to_iso_string,
	is_date_string_valid,
	timestr_to_time,
	validate_datatype
)
from temporal_lib.tlib_date import TDate, date_to_week_tuple
from temporal_lib.tlib_week import Week, week_generator
from temporal_lib.tlib_weekday import (
	next_weekday_after_date,
	WEEKDAYS_SUN0,
	WEEKDAYS_MON0,
	weekday_string_to_shortname,
	weekday_int_from_name
)

# Frappe modules.
import frappe
from frappe import _, throw, msgprint, ValidationError  # noqa F401

# Temporal
from temporal import core
from temporal import redis as temporal_redis  # alias to distinguish from Third Party module

# Constants
__version__ = '13.3.0'

# Epoch is the range of 'business active' dates.
EPOCH_START_YEAR = 2020
EPOCH_END_YEAR = 2050
EPOCH_START_DATE = DateType(EPOCH_START_YEAR, 1, 1)
EPOCH_END_DATE = DateType(EPOCH_END_YEAR, 12, 31)

# These should be considered true Min/Max for all other calculations.
MIN_YEAR = 2000
MAX_YEAR = 2201
MIN_DATE = DateType(MIN_YEAR, 1, 1)
MAX_DATE = DateType(MAX_YEAR, 12, 31)

# Module Typing: https://docs.python.org/3.8/library/typing.html#module-typing

class ArgumentMissing(ValidationError):
	http_status_code = 500

class ArgumentType(ValidationError):
	http_status_code = 500


class Builder():
	"""
	This class is used to build the Temporal data (stored in Redis Cache)
	"""

	def __init__(self, epoch_year, end_year, start_of_week='SUN'):
		"""
		Initialize the Builder class.
		"""

		# This determines if we output additional Error Messages.
		self.debug_mode = frappe.db.get_single_value('Temporal Manager', 'debug_mode')

		if not isinstance(start_of_week, str):
			raise TypeError("Argument 'start_of_week' should be a Python String.")
		if start_of_week not in ('SUN', 'MON'):
			raise ValueError(f"Argument 'start of week' must be either 'SUN' or 'MON' (value passed was '{start_of_week}'")
		if start_of_week != 'SUN':
			raise NotImplementedError("Temporal is not-yet coded to handle weeks that begin with Monday.")

		# Starting and Ending Year
		if not epoch_year:
			gui_start_year = int(frappe.db.get_single_value('Temporal Manager', 'start_year') or 0)
			epoch_year = gui_start_year or EPOCH_START_YEAR
		if not end_year:
			gui_end_year = int(frappe.db.get_single_value('Temporal Manager', 'end_year') or 0)
			end_year = gui_end_year or EPOCH_END_YEAR
		if end_year < epoch_year:
			raise ValueError(f"Ending year {end_year} cannot be smaller than Starting year {epoch_year}")
		self.epoch_year = epoch_year
		self.end_year = end_year

		year_range = range(self.epoch_year, self.end_year + 1)  # because Python ranges are not inclusive
		self.years = tuple(year_range)
		self.weekday_names = WEEKDAYS_SUN0 if start_of_week == 'SUN' else WEEKDAYS_MON0
		self.week_dicts = []  # this will get populated as we build.

	@staticmethod
	@frappe.whitelist()
	def build_all(epoch_year=None, end_year=None, start_of_week='SUN'):
		""" Rebuild all Temporal cache key-values. """
		instance = Builder(epoch_year=epoch_year,
		                   end_year=end_year,
		                   start_of_week=start_of_week)

		instance.build_weeks()  # must happen first, so we can build years more-easily.
		instance.build_years()
		instance.build_days()

	def build_years(self):
		"""
		Calculate years and write to Redis.
		"""
		temporal_redis.write_years(self.years, self.debug_mode)
		for year in self.years:
			self.build_year(year)

	def build_year(self, year):
		"""
		Create a dictionary of Year metadata and write to Redis.
		"""
		date_start = DateType(year, 1, 1)
		date_end = DateType(year, 12, 31)
		days_in_year = (date_end - date_start).days + 1
		jan_one_dayname = date_start.strftime("%a").upper()
		year_dict = {}
		year_dict['year'] = year
		year_dict['date_start'] = date_start.strftime("%m/%d/%Y")
		year_dict['date_end'] = date_end.strftime("%m/%d/%Y")
		year_dict['days_in_year'] = days_in_year
		# What day of the week is January 1st?
		year_dict['jan_one_dayname'] = jan_one_dayname
		try:
			weekday_short_names = tuple(weekday['name_short'] for weekday in self.weekday_names)
			year_dict['jan_one_weekpos'] = weekday_short_names.index(jan_one_dayname) + 1  # because zero-based indexing
		except ValueError as ex:
			raise ValueError(f"Could not find value '{jan_one_dayname}' in tuple 'self.weekday_names' = {self.weekday_names}") from ex
		# Get the maximum week number (52 or 53)
		max_week_number = max(week['week_number'] for week in self.week_dicts if week['year'] == year)
		year_dict['max_week_number'] = max_week_number

		temporal_redis.write_single_year(year_dict, self.debug_mode)

	def build_days(self):
		start_date = DateType(self.epoch_year, 1, 1)  # could also do self.years[0]
		end_date = DateType(self.end_year, 12, 31)  # could also do self.years[-1]

		count = 0
		for date_foo in date_range(start_date, end_date):
			day_dict = {}
			day_dict['date'] = date_foo
			day_dict['date_as_string'] = day_dict['date'].strftime("%Y-%m-%d")
			day_dict['weekday_name'] = date_foo.strftime("%A")
			day_dict['weekday_name_short'] = date_foo.strftime("%a")
			day_dict['day_of_month'] = date_foo.strftime("%d")
			day_dict['month_in_year_int'] = date_foo.strftime("%m")
			day_dict['month_in_year_str'] = date_foo.strftime("%B")
			day_dict['year'] = date_foo.year
			day_dict['day_of_year'] = date_foo.strftime("%j")
			# Calculate the week number:
			week_tuple = date_to_week_tuple(date_foo, verbose=False)  # previously self.debug_mode
			day_dict['week_year'] = week_tuple[0]
			day_dict['week_number'] = week_tuple[1]
			day_dict['index_in_week'] = int(date_foo.strftime("%w")) + 1  # 1-based indexing
			# Write this dictionary in the Redis cache:
			temporal_redis.write_single_day(day_dict)
			count += 1
		if self.debug_mode:
			print(f"\u2713 Created {count} Temporal Day keys in Redis.")

	def build_weeks(self):
		"""
		Build all the weeks between Epoch Date and End Date
		"""
		# Begin on January 1st
		jan1_date = DateType(self.epoch_year, 1, 1)
		jan1_day_of_week = int(jan1_date.strftime("%w"))  # day of week for January 1st

		week_start_date = jan1_date - timedelta(days=jan1_day_of_week)  # if January 1st is not Sunday, back up.
		week_end_date = None
		week_number = None
		print(f"Temporal is building weeks, starting with {week_start_date}")

		if self.debug_mode:
			print(f"Processing weeks begining with calendar date: {week_start_date}")

		count = 0
		while True:
			# Stop once week_start_date's year exceeds the Maximum Year.
			if week_start_date.year > self.end_year:
				if self.debug_mode:
					print(f"Ending loop on {week_start_date}")
				break

			week_end_date = week_start_date + timedelta(days=6)
			if self.debug_mode:
				print(f"Week's end date = {week_end_date}")
			if (week_start_date.day == 1) and (week_start_date.month == 1):
				# Sunday is January 1st, it's a new year.
				week_number = 1
			elif week_end_date.year > week_start_date.year:
				# January 1st falls somewhere inside the week
				week_number = 1
			else:
				week_number += 1
			tuple_of_dates = tuple(list(date_range(week_start_date, week_end_date)))
			if self.debug_mode:
				print(f"Writing week number {week_number}")
			week_dict = {}
			week_dict['year'] = week_end_date.year
			week_dict['week_number'] = week_number
			week_dict['week_start'] = week_start_date
			week_dict['week_end'] = week_end_date
			week_dict['week_dates'] = tuple_of_dates
			temporal_redis.write_single_week(week_dict)
			self.week_dicts.append(week_dict)  # internal object in Builder, for use later in build_years

			# Increment to the Next Week
			week_start_date = week_start_date + timedelta(days=7)
			count += 1

		# Loop complete.
		if self.debug_mode:
			print(f"\u2713 Created {count} Temporal Week keys in Redis.")


def get_year_from_frappedate(frappe_date):
	return int(frappe_date[:4])


def date_to_datekey(any_date):
	"""
	Create a Redis key from any date value.
	"""
	if not isinstance(any_date, datetime.date):
		raise TypeError(f"Argument 'any_date' should have type 'datetime.date', not '{type(any_date)}'")
	date_as_string = any_date.strftime("%Y-%m-%d")
	return f"temporal/day/{date_as_string}"


# ----------------
# Weeks
# ----------------

def week_to_weekkey(year, week_number):
	"""
	Create a Redis key from any week tuple.
	"""
	if not isinstance(week_number, int):
		raise TypeError("Argument 'week_number' should be a Python integer.")
	week_as_string = str(week_number).zfill(2)
	return f"temporal/week/{year}-{week_as_string}"


def get_week_by_weeknum(year, week_number):
	"""
	Returns a class Week.
	"""
	week_dict = temporal_redis.read_single_week(year, week_number, )

	if not week_dict:
		print(f"Warning: No value in Redis for year {year}, week number {week_number}.  Rebuilding...")
		Builder.build_all()
		if (not week_dict) and frappe.db.get_single_value('Temporal Manager', 'debug_mode'):
			raise KeyError(f"WARNING: Unable to find Week in Redis for year {year}, week {week_number}.")
		return None

	return Week((year, week_number))


@frappe.whitelist()
def get_weeks_as_dict(from_year, from_week_num, to_year, to_week_num):
	""" Given a range of Week numbers, return a List of dictionaries.

		From terminal: bench execute --args "2021,15,20" temporal.get_weeks_as_dict

	"""
	return temporal_lib.tlib_week.get_weeks_as_dict(from_year, from_week_num, to_year, to_week_num)


def date_to_scalar(any_date):
	"""
	It makes zero difference what particular Integers we use to represent calendar dates, so long as:
		1. They are consistent throughout multiple calls/calculations.
		2. There are no gaps between calendar days.

	Given all the calendar dates stored in a Table, a simple identity column would suffice.
	"""
	scalar_value = frappe.db.get_value("Temporal Dates", filters={"calendar_date": any_date}, fieldname="scalar_value", cache=True)
	return scalar_value
