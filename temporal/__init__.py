""" temporal.py """

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# Standard Library
import datetime
from datetime import timedelta
from datetime import date as dtdate, datetime as datetime_type

# Third Party
import dateutil.parser  # https://stackoverflow.com/questions/48632176/python-dateutil-attributeerror-module-dateutil-has-no-attribute-parse
from dateutil.relativedelta import relativedelta
from dateutil.rrule import SU, MO, TU, WE, TH, FR, SA  # noqa F401

# Temporal Lib
import temporal_lib

from temporal_lib import int_to_ordinal_string as make_ordinal
from temporal_lib.core import (
	localize_datetime,
	date_is_between, date_range,
	date_range_from_strdates, calc_future_dates
)
from temporal_lib.tlib_date import TDate, date_to_week_tuple
from temporal_lib.tlib_week import Week
from temporal_lib.tlib_weekday import (
	WEEKDAYS_SUN0, WEEKDAYS_MON0,
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
__version__ = '13.2.0'

# Epoch is the range of 'business active' dates.
EPOCH_START_YEAR = 2020
EPOCH_END_YEAR = 2050
EPOCH_START_DATE = dtdate(EPOCH_START_YEAR, 1, 1)
EPOCH_END_DATE = dtdate(EPOCH_END_YEAR, 12, 31)

# These should be considered true Min/Max for all other calculations.
MIN_YEAR = 2000
MAX_YEAR = 2201
MIN_DATE = dtdate(MIN_YEAR, 1, 1)
MAX_DATE = dtdate(MAX_YEAR, 12, 31)

# Module Typing: https://docs.python.org/3.8/library/typing.html#module-typing

class ArgumentMissing(ValidationError):
	http_status_code = 500

class ArgumentType(ValidationError):
	http_status_code = 500


class Builder():
	"""
	This class is used to build the Temporal data (stored in Redis Cache) """

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
		""" Calculate years and write to Redis. """
		temporal_redis.write_years(self.years, self.debug_mode)
		for year in self.years:
			self.build_year(year)

	def build_year(self, year):
		""" Create a dictionary of Year metadata and write to Redis. """
		date_start = dtdate(year, 1, 1)
		date_end = dtdate(year, 12, 31)
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
		start_date = dtdate(self.epoch_year, 1, 1)  # could also do self.years[0]
		end_date = dtdate(self.end_year, 12, 31)  # could also do self.years[-1]

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
			week_tuple = Internals.date_to_week_tuple(date_foo, verbose=False)  # previously self.debug_mode
			day_dict['week_year'] = week_tuple[0]
			day_dict['week_number'] = week_tuple[1]
			day_dict['index_in_week'] = int(date_foo.strftime("%w")) + 1  # 1-based indexing
			# Write this dictionary in the Redis cache:
			temporal_redis.write_single_day(day_dict)
			count += 1
		if self.debug_mode:
			print(f"\u2713 Created {count} Temporal Day keys in Redis.")

	def build_weeks(self):
		""" Build all the weeks between Epoch Date and End Date """
		# Begin on January 1st
		jan1_date = dtdate(self.epoch_year, 1, 1)
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


def date_generator_type_1(start_date, increments_of, earliest_result_date):
	"""
	Given a start date, increment N number of days.
	First result can be no earlier than 'earliest_result_date'
	"""
	iterations = 0
	next_date = start_date
	while True:
		iterations += 1
		if (iterations == 1) and (start_date == earliest_result_date):  # On First Iteration, if dates match, yield Start Date.
			yield start_date
		else:
			next_date = next_date + timedelta(days=increments_of)
			if next_date >= earliest_result_date:
				yield next_date


def date_to_datekey(any_date):
	if not isinstance(any_date, datetime.date):
		raise TypeError(f"Argument 'any_date' should have type 'datetime.date', not '{type(any_date)}'")
	date_as_string = any_date.strftime("%Y-%m-%d")
	return f"temporal/day/{date_as_string}"


def get_calendar_years():
	""" Fetch calendar years from Redis. """
	return temporal_redis.read_years()


def get_calendar_year(year):
	""" 
	Fetch a Year dictionary from Redis.
	"""
	return temporal_redis.read_single_year(year)

# ----------------
# Weeks
# ----------------

def week_to_weekkey(year, week_number):
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


def get_week_by_anydate(any_date):
	"""
	Given a datetime date, returns a class instance 'Week'
	"""
	return Week.date_to_week(any_date)

@frappe.whitelist()
def get_weeks_as_dict(year, from_week_num, to_week_num):
	""" Given a range of Week numbers, return a List of dictionaries.

		From Shell: bench execute --args "2021,15,20" temporal.get_weeks_as_dict

	"""
	# Convert JS strings into integers.
	year = int(year)
	from_week_num = int(from_week_num)
	to_week_num = int(to_week_num)

	if year not in range(MIN_YEAR, MAX_YEAR):
		raise Exception(f"Invalid value '{year}' for argument 'year'")
	if from_week_num not in range(1, 54):  # 53 possible week numbers.
		raise Exception(f"Invalid value '{from_week_num}' for argument 'from_week_num'")
	if to_week_num not in range(1, 54):  # 53 possible week numbers.
		raise Exception(f"Invalid value '{to_week_num}' for argument 'to_week_num'")

	weeks_list = []
	for week_num in range(from_week_num, to_week_num + 1):
		week_dict = temporal_redis.read_single_week(year, week_num)
		if week_dict:
			weeks_list.append(week_dict)

	return weeks_list


def datestr_to_week_number(date_as_string):
	""" Given a string date, return the Week Number. """
	return Internals.date_to_week_tuple(datestr_to_date(date_as_string), verbose=False)


def week_generator(from_date, to_date):
	"""
	Return a Python Generator for all the weeks in a date range.
	"""
	from_date = any_to_date(from_date)
	to_date = any_to_date(to_date)

	if from_date > to_date:
		raise ValueError("Argument 'from_date' cannot be greater than argument 'to_date'")
	# If dates are the same, simply return the 1 week.
	if from_date == to_date:
		yield get_week_by_anydate(from_date)

	from_week = get_week_by_anydate(from_date)  # Class of type 'Week'
	if not from_week:
		raise Exception(f"Unable to find a Week for date {from_date}. (Temporal week_generator() and Cache)")
	to_week = get_week_by_anydate(to_date)  # Class of type 'Week'
	if not to_week:
		raise Exception(f"Unable to find a Week for date {to_date} (Temporal week_generator() and Cache)")

	# results = []

	# Determine which Week Numbers are missing.
	for year in range(from_week.week_year, to_week.week_year + 1):
		# print(f"Processing week in year {year}")
		year_dict = temporal_redis.read_single_year(year)
		# Start Index
		start_index = 0
		if year == from_week.week_year:
			start_index = from_week.week_number
		else:
			start_index = 1
		# End Index
		end_index = 0
		if year == to_week.week_year:
			end_index = to_week.week_number
		else:
			end_index = year_dict['max_week_number']

		for week_num in range(start_index, end_index + 1):
			yield get_week_by_weeknum(year, week_num)  # A class of type 'Week'


# ----------------
# OTHER
# ----------------

def get_date_metadata(any_date):
	""" This function returns a date dictionary from Redis.

		bench execute --args "{'2021-04-18'}" temporal.get_date_metadata

	 """
	if isinstance(any_date, str):
		any_date = datetime.datetime.strptime(any_date, '%Y-%m-%d').date()
	if not isinstance(any_date, datetime.date):
		raise TypeError(f"Argument 'any_date' should have type 'datetime.date', not '{type(any_date)}'")

	return temporal_redis.read_single_day(date_to_datekey(any_date))

def get_earliest_date(list_of_dates):
	if not all(isinstance(x, datetime.date) for x in list_of_dates):
		raise ValueError("All values in argument must be datetime dates.")
	return min(list_of_dates)

def get_latest_date(list_of_dates):
	if not all(isinstance(x, datetime.date) for x in list_of_dates):
		raise ValueError("All values in argument must be datetime dates.")
	return max(list_of_dates)

# ----------------
# DATETIME and STRING CONVERSION
# ----------------

def any_to_date(date_as_unknown):
	"""
	Given an argument of unknown Type, try to return a Date.
	"""
	try:
		if not date_as_unknown:
			return None
		if isinstance(date_as_unknown, str):
			return datetime.datetime.strptime(date_as_unknown,"%Y-%m-%d").date()
		if isinstance(date_as_unknown, datetime.date):
			return date_as_unknown

	except dateutil.parser._parser.ParserError as ex:  # pylint: disable=protected-access
		raise ValueError(f"'{date_as_unknown}' is not a valid date string.") from ex

	raise TypeError(f"Unhandled type ({type(date_as_unknown)}) for argument to function any_to_date()")

def any_to_time(generic_time):
	"""
	Given an argument of a generic, unknown Type, try to return a Time.
	"""
	try:
		if not generic_time:
			return None
		if isinstance(generic_time, str):
			return timestr_to_time(generic_time)
		if isinstance(generic_time, datetime.time):
			return generic_time

	except dateutil.parser._parser.ParserError as ex:  # pylint: disable=protected-access
		raise ValueError(f"'{generic_time}' is not a valid Time string.") from ex

	raise TypeError(f"Function argument 'generic_time' in any_to_time() has an unhandled data type: '{type(generic_time)}'")

def any_to_datetime(datetime_as_unknown):
	"""
	Given an argument of unknown Type, try to return a DateTime.
	"""
	datetime_string_format = "%Y-%m-%d %H:%M:%S"
	try:
		if not datetime_as_unknown:
			return None
		if isinstance(datetime_as_unknown, str):
			return datetime.datetime.strptime(datetime_as_unknown, datetime_string_format)
		if isinstance(datetime_as_unknown, datetime.datetime):
			return datetime_as_unknown

	except dateutil.parser._parser.ParserError as ex:  # pylint: disable=protected-access
		raise ValueError(f"'{datetime_as_unknown}' is not a valid datetime string.") from ex

	raise TypeError(f"Unhandled type ({type(datetime_as_unknown)}) for argument to function any_to_datetime()")

def any_to_iso_date_string(any_date):
	"""
	Given a date, create a String that MariaDB understands for queries (YYYY-MM-DD)
	"""
	if isinstance(any_date, datetime.date):
		return any_date.strftime("%Y-%m-%d")
	if isinstance(any_date, str):
		return any_date
	raise Exception(f"Argument 'any_date' can be a String or datetime.date only (found '{type(any_date)}')")

def datestr_to_date(date_as_string):
	"""
	Converts string date (YYYY-MM-DD) to datetime.date object.
	"""

	# ERPNext is very inconsistent with Date typing.  We should handle several possibilities:
	if not date_as_string:
		return None
	if isinstance(date_as_string, datetime.date):
		return date_as_string
	if not isinstance(date_as_string, str):
		raise TypeError(f"Argument 'date_as_string' should be of type String, not '{type(date_as_string)}'")
	if not is_date_string_valid(date_as_string):
		return None

	try:
		# Explicit is Better than Implicit.  The format should be YYYY-MM-DD.

		# The function below is completely asinine.
		# If you pass a day of week string (e.g. "Friday"), it returns the next Friday in the calendar.  Instead of an error.
		# return dateutil.parser.parse(date_as_string, yearfirst=True, dayfirst=False).date()

		# So I'm now using this instead.
		return datetime.datetime.strptime(date_as_string,"%Y-%m-%d").date()

	except dateutil.parser._parser.ParserError as ex:  # pylint: disable=protected-access
		raise ValueError("Value '{date_as_string}' is not a valid date string.") from ex

def date_to_iso_string(any_date):
	"""
	Given a date, create an ISO String.  For example, 2021-12-26.
	"""
	if not isinstance(any_date, datetime.date):
		raise Exception(f"Argument 'any_date' should have type 'datetime.date', not '{type(any_date)}'")
	return any_date.strftime("%Y-%m-%d")

def datetime_to_iso_string(any_datetime):
	"""
	Given a datetime, create a ISO String
	"""
	if not isinstance(any_datetime, datetime_type):
		raise Exception(f"Argument 'any_date' should have type 'datetime', not '{type(any_datetime)}'")

	return any_datetime.isoformat(sep=' ')  # Note: Frappe not using 'T' as a separator, but a space ''

def is_date_string_valid(date_string):
	# dateutil parser does not agree with dates like "0001-01-01" or "0000-00-00"
	if (not date_string) or (date_string or "").startswith(("0001-01-01", "0000-00-00")):
		return False
	return True

def timestr_to_time(time_as_string):
	"""
	Converts a string time (8:30pm) to datetime.time object.
	Examples:
		8pm
		830pm
		830 pm
		8:30pm
		20:30
		8:30 pm
	"""
	time_as_string = time_as_string.lower()
	time_as_string = time_as_string.replace(':', '')
	time_as_string = time_as_string.replace(' ', '')

	am_pm = None
	hour = None
	minute = None

	if 'am' in time_as_string:
		am_pm = 'am'
		time_as_string = time_as_string.replace('am', '')
	elif 'pm' in time_as_string:
		am_pm = 'pm'
		time_as_string = time_as_string.replace('pm', '')
	time_as_string = time_as_string.replace(' ', '')

	# Based on length of string, make some assumptions:
	if len(time_as_string) == 0:
		raise ValueError(f"Invalid time string '{time_as_string}'")
	if len(time_as_string) == 1:
		hour = time_as_string
		minute = 0
	elif len(time_as_string) == 2:
		raise ValueError(f"Invalid time string '{time_as_string}'")
	elif len(time_as_string) == 3:
		hour = time_as_string[0]
		minute = time_as_string[1:3]  # NOTE: Python string splicing; last index is not included.
	elif len(time_as_string) == 4:
		hour = time_as_string[0:2]  # NOTE: Python string splicing; last index is not included.
		minute = time_as_string[2:4] # NOTE: Python string splicing; last index is not included.
		if int(hour) > 12 and am_pm == 'am':
			raise ValueError(f"Invalid time string '{time_as_string}'")
	else:
		raise ValueError(f"Invalid time string '{time_as_string}'")

	if not am_pm:
		if int(hour) > 12:
			am_pm = 'pm'
		else:
			am_pm = 'am'
	if am_pm == 'pm':
		hour = int(hour) + 12

	return datetime.time(int(hour), int(minute), 0)

# ----------------
# Weekdays
# ----------------

def next_weekday_after_date(weekday, any_date):
	"""
	Find the next day of week (MON, SUN, etc) after a target date.
	"""
	weekday_int = None
	if isinstance(weekday, int):
		weekday_int = weekday
	elif isinstance(weekday, str):
		weekday_int = weekday_int_from_name(weekday, first_day_of_week='MON')  # Monday-based math below

	days_ahead = weekday_int - any_date.weekday()
	if days_ahead <= 0:  # Target day already happened this week
		days_ahead += 7
	return any_date + datetime.timedelta(days_ahead)


def validate_datatype(argument_name, argument_value, expected_type, mandatory=False):
	"""
	A helpful generic function for checking a variable's datatype, and throwing an error on mismatches.
	Absolutely necessary when dealing with extremely complex Python programs that talk to SQL, HTTP, Redis, etc.

	NOTE: expected_type can be a single Type, or a tuple of Types.
	"""
	# Throw error if missing mandatory argument.
	NoneType = type(None)
	if mandatory and isinstance(argument_value, NoneType):
		raise ArgumentMissing(f"Argument '{argument_name}' is mandatory.")

	if not argument_value:
		return argument_value  # datatype is going to be a NoneType, which is okay if not mandatory.

	# Check argument type
	if not isinstance(argument_value, expected_type):
		if isinstance(expected_type, tuple):
			expected_type_names = [ each.__name__ for each in expected_type ]
			msg = f"Argument '{argument_name}' should be one of these types: '{', '.join(expected_type_names)}'"
			msg += f"<br>Found a {type(argument_value).__name__} with value '{argument_value}' instead."
		else:
			msg = f"Argument '{argument_name}' should be of type = '{expected_type.__name__}'"
			msg += f"<br>Found a {type(argument_value).__name__} with value '{argument_value}' instead."
		raise ArgumentType(msg)

	# Otherwise, return the argument to the caller.
	return argument_value

def date_to_datetime(any_date):
	"""
	Return a Date as a Datetime set to midnight.
	"""
	return datetime_type.combine(any_date, datetime_type.min.time())

def date_to_scalar(any_date):
	"""
	It makes zero difference what particular Integers we use to represent calendar dates, so long as:
		1. They are consistent throughout multiple calls/calculations.
		2. There are no gaps between calendar days.

	Given all the calendar dates stored in a Table, a simple identity column would suffice.
	"""
	scalar_value = frappe.db.get_value("Temporal Dates", filters={"calendar_date": any_date}, fieldname="scalar_value", cache=True)
	return scalar_value
