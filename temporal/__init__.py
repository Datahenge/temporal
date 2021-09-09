""" temporal/temporal/__init__.py """

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# Standard Library
import datetime
from datetime import timedelta
from datetime import date as dtdate

# Third Party
import dateutil
from dateutil.relativedelta import relativedelta
from dateutil.rrule import SU, MO, TU, WE, TH, FR, SA  # noqa F401

# Frappe modules.
import frappe
from frappe import _, throw, msgprint  # noqa F401

# Temporal
from temporal import redis as temporal_redis  # alias to distinguish from Third Party module

# Constants
__version__ = '13.0.0'
EPOCH_YEAR = 2020
END_YEAR = 2050
MIN_YEAR = 2000
MAX_YEAR = 2201

# Module Typing: https://docs.python.org/3.8/library/typing.html#module-typing

WEEKDAYS = (
	{ 'name_short': 'SUN', 'name_long': 'Sunday' },
	{ 'name_short': 'MON', 'name_long': 'Monday' },
	{ 'name_short': 'TUE', 'name_long': 'Tuesday' },
	{ 'name_short': 'WED', 'name_long': 'Wednesday' },
	{ 'name_short': 'THU', 'name_long': 'Thursday' },
	{ 'name_short': 'FRI', 'name_long': 'Friday' },
	{ 'name_short': 'SAT', 'name_long': 'Saturday' },
)

WEEKDAYS_SUN0 = (
	{ 'pos': 0, 'name_short': 'SUN', 'name_long': 'Sunday' },
	{ 'pos': 1, 'name_short': 'MON', 'name_long': 'Monday' },
	{ 'pos': 2, 'name_short': 'TUE', 'name_long': 'Tuesday' },
	{ 'pos': 3, 'name_short': 'WED', 'name_long': 'Wednesday' },
	{ 'pos': 4, 'name_short': 'THU', 'name_long': 'Thursday' },
	{ 'pos': 5, 'name_short': 'FRI', 'name_long': 'Friday' },
	{ 'pos': 6, 'name_short': 'SAT', 'name_long': 'Saturday' })

WEEKDAYS_MON0 = (
	{ 'pos': 0, 'name_short': 'MON', 'name_long': 'Monday' },
	{ 'pos': 1, 'name_short': 'TUE', 'name_long': 'Tuesday' },
	{ 'pos': 2, 'name_short': 'WED', 'name_long': 'Wednesday' },
	{ 'pos': 3, 'name_short': 'THU', 'name_long': 'Thursday' },
	{ 'pos': 4, 'name_short': 'FRI', 'name_long': 'Friday' },
	{ 'pos': 5, 'name_short': 'SAT', 'name_long': 'Saturday' },
	{ 'pos': 6, 'name_short': 'SUN', 'name_long': 'Sunday' })

# WEEKDAYS_SUN = ( 'SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT')
# WEEKDAYS_SUNDAY = ( 'Sunday', 'Monday', 'Tuedsay', 'Wednesday', 'Thursday', 'Friday', 'Saturday')
# WEEKDAYS_MON = ( 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN')


def validate_datatype(argument_name, argument_value, expected_type, mandatory=False):
	"""
	A helpful generic function for checking a variable's datatype, and throwing an error on mismatches.
	Absolutely necessary when dealing with extremely complex Python programs that talk to SQL, HTTP, Redis, etc.
	"""
	if mandatory and (not argument_value):
		raise ValueError(f"Argument '{argument_name}' is mandatory.")
	if not argument_value:
		return  # datatype is going to be a NoneType, which is okay if not mandatory.
	if not isinstance(argument_value, expected_type):
		msg = f"Argument '{argument_name}' should be of type = '{expected_type.__name__}'"
		msg += f"<br>Found a {type(argument_value).__name__} with value '{argument_value}' instead."
		raise TypeError(msg)


class TDate():
	""" A better datetime.date """
	def __init__(self, any_date):
		if not any_date:
			raise TypeError("Class argument 'any_date' cannot be None.")
		if not isinstance(any_date, datetime.date):
			raise TypeError("Class argument 'any_date' must be a Python date.")
		self.date = any_date

	def __add__(self, other):
		# operator overload:  adding two TDates
		return self.date + other.date

	def __sub__(self, other):
		# operator overload: subtracting two TDates
		return self.date - other.date

	def day_of_week_int(self, zero_based=False):
		""" Return an integer representing Day of Week (beginning with Sunday) """
		if zero_based:
			return self.date.toordinal() % 7  # Sunday being the 0th day of week
		return (self.date.toordinal() % 7) + 1  # Sunday being the 1st day of week

	def day_of_week_shortname(self):
		return WEEKDAYS_SUN0[self.day_of_week_int() - 1]['name_short']

	def day_of_week_longname(self):
		return WEEKDAYS_SUN0[self.day_of_week_int() - 1]['name_long']

	def day_of_month(self):
		return self.date.day

	def day_of_year(self):
		return int(self.date.strftime("%j"))  # e.g. April 1st is the 109th day in year 2020.

	def month_of_year(self):
		return self.date.month

	def year(self):
		return self.date.year

	def as_date(self):
		return self.date

	def jan1(self):
		return TDate(dtdate(year=self.date.year, month=1, day=1))

	def jan1_next_year(self):
		return TDate(dtdate(year=self.date.year + 1, month=1, day=1))

	def is_between(self, from_date, to_date):
		return from_date <= self.date <= to_date


class Week():
	""" A calendar week, starting on Sunday, where the week containing January 1st is always week #1 """
	def __init__(self, week_year, week_number, set_of_days, date_start, date_end):
		self.week_year = week_year
		self.week_number = week_number
		self.week_number_str = str(self.week_number).zfill(2)
		self.days = set_of_days
		self.date_start = date_start
		self.date_end = date_end


class Builder():
	""" This class is used to build the temporal data (which we're storing in Redis) """

	def __init__(self, epoch_year, end_year, start_of_week='SUN'):
		""" Initialize the Builder """

		# This determines if we output additional Error Messages.
		self.debug_mode = frappe.db.get_single_value('Temporal Manager', 'debug_mode')

		if not isinstance(start_of_week, str):
			raise TypeError("Argument 'start_of_week' should be a Python String.")
		if start_of_week not in ('SUN', 'MON'):
			raise ValueError(f"Argument 'start of week' must be either 'SUN' or 'MON' (value passed was '{start_of_week}'")
		if start_of_week != 'SUN':
			raise Exception("Temporal is not-yet coded to handle weeks that begin with Monday.")

		# Starting and Ending Year
		if not epoch_year:
			gui_start_year = int(frappe.db.get_single_value('Temporal Manager', 'start_year') or 0)
			epoch_year = gui_start_year or EPOCH_YEAR
		if not end_year:
			gui_end_year = int(frappe.db.get_single_value('Temporal Manager', 'end_year') or 0)
			end_year = gui_end_year or END_YEAR
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
			week_tuple = Internals.date_to_week_tuple(date_foo, verbose=self.debug_mode)
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

		if self.debug_mode:
			print(f"Processing weeks begining with calendar date: {week_start_date}")

		count = 0
		while True:
			# Stop once week_start_date's year exceeds the Maximum Year.
			if week_start_date.year > self.end_year:
				break

			week_end_date = week_start_date + timedelta(days=6)
			if (week_start_date.day == 1) and (week_start_date.month == 1):
				# Sunday is January 1st, it's a new year.
				week_number = 1
			elif week_end_date.year > week_start_date.year:
				# January 1st falls somewhere inside the week
				week_number = 1
			else:
				week_number += 1
			tuple_of_dates = tuple(list(date_range(week_start_date, week_end_date)))
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


class Internals():
	""" Internal functions that should not be called outside of Temporal. """
	@staticmethod
	def date_to_week_tuple(any_date, verbose=False):
		""" Given a date, return the corresponding week number.
			This uses a special calculation, that prevents "partial weeks"
		"""
		if not isinstance(any_date, datetime.date):
			raise TypeError("Argument must be of type 'datetime.date'")

		any_date = TDate(any_date)  # recast as a Temporal TDate
		jan1 = any_date.jan1()
		jan1_next = any_date.jan1_next_year()

		if verbose:
			print("\n----Verbose Details----")
			print(f"January 1st {jan1.as_date().year} is the {jan1.day_of_week()} day in the week.")
			print(f"January 1st {jan1_next.as_date().year} is the {jan1_next.day_of_week()} day in the week.")
			print(f"Day of Week: {any_date.day_of_week()}")
			print(f"Distance from Jan 1st: {(any_date-jan1).days} days")
			print(f"Distance from Future Jan 1st: {(jan1_next-any_date).days} days")
		# SCENARIO 1: January 1st
		if (any_date.day_of_month() == 1) and (any_date.month_of_year() == 1):
			return (any_date.year(), 1)
		# SCENARIO 2A: Week 1, after January 1st
		if  ( any_date.day_of_week_int() > jan1.day_of_week_int() ) and \
			( (any_date - jan1).days in range(1, 7)):
			if verbose:
				print("Scenario 2A; target date part of Week 1.")
			return (any_date.year(), 1)
		# SCENARIO 2B: Week 1, before NEXT January 1st
		if  ( any_date.day_of_week_int() < jan1_next.day_of_week_int() ) and \
			( (jan1_next - any_date).days in range(1, 7)):
			if verbose:
				print("Scenario 2B; target date near beginning of Future Week 1.")
			return (any_date.year() + 1, 1)
		# SCENARIO 3:  Find the first Sunday, then modulus 7.
		if verbose:
			print("Scenario 3: Target date is not nearby to January 1st.")
		first_sunday = TDate(jan1.as_date() + relativedelta(weekday=SU))
		first_sunday_pos = first_sunday.day_of_year()
		# Formula: (( Date's Position in Year - Position of First Sunday) / 7 ) + 2
		# Why the +2 at the end?  Because +1 for modulus, and +1 because we're offset against Week #2
		week_number = int((any_date.day_of_year() - first_sunday_pos) / 7 ) + 2
		return (jan1.year(), week_number)

	@staticmethod
	def get_year_from_frappedate(frappe_date):
		return int(frappe_date[:4])


# ----------------
# Public Functions
# ----------------

def date_range(start_date, end_date):
	""" Generator for an inclusive range of dates.
		It's pretty silly this isn't part of Python Standard Library or datetime
	"""
	# Important to add +1, otherwise the range is -not- inclusive.
	for number_of_days in range(int((end_date - start_date).days) + 1):
		yield start_date + timedelta(number_of_days)


def date_range_from_strdates(start_date_str, end_date_str):
	""" Generator for an inclusive range of date-strings. """
	if not isinstance(start_date_str, str):
		raise TypeError("Argument 'start_date_str' must be a Python string.")
	if not isinstance(end_date_str, str):
		raise TypeError("Argument 'end_date_str' must be a Python string.")
	start_date = datestr_to_date(start_date_str)
	end_date = datestr_to_date(end_date_str)
	return date_range(start_date, end_date)


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


def calc_future_dates(epoch_date, multiple_of_days, earliest_result_date, qty_of_result_dates):
	"""
		Purpose: Predict future dates, based on an epoch date and multiple.
		Returns: A List of Dates

		Arguments
		epoch_date:           The date from which the calculation begins.
		multiple_of_days:     In every iteration, how many days do we move forward?
		no_earlier_than:      What is earliest result date we want to see?
		qty_of_result_dates:  How many qualifying dates should this function return?
	"""
	# Convert to dates, always.
	epoch_date = any_to_date(epoch_date)
	earliest_result_date = any_to_date(earliest_result_date)
	# Validate the remaining data types.
	validate_datatype("multiple_of_days", multiple_of_days, int)
	validate_datatype("qty_of_result_dates", qty_of_result_dates, int)

	if earliest_result_date < epoch_date:
		raise ValueError("The 'earliest_result_date' cannot precede the 'epoch_date'")

	this_generator = date_generator_type_1(epoch_date, multiple_of_days, earliest_result_date)
	ret = []
	for _ in range(qty_of_result_dates):  # underscore because we don't actually need the index.
		ret.append(next(this_generator))
	return ret


def date_to_datekey(any_date):
	if not isinstance(any_date, datetime.date):
		raise Exception(f"Argument 'any_date' should have type 'datetime.date', not '{type(any_date)}'")
	date_as_string = any_date.strftime("%Y-%m-%d")
	return f"temporal/day/{date_as_string}"


def get_calendar_years():
	""" Fetch calendar years from Redis. """
	return temporal_redis.read_years()


def get_calendar_year(year):
	""" Fetch a Year dictionary from Redis. """
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
	"""  Returns a class Week. """
	week_dict = temporal_redis.read_single_week(year, week_number, )
	if not week_dict:
		if frappe.db.get_single_value('Temporal Manager', 'debug_mode'):
			raise KeyError(f"WARNING: Unable to find Week in Redis for year {year}, week {week_number}.")
		return None
	return Week(week_dict['year'],
	            week_dict['week_number'],
	            week_dict['week_dates'],
	            week_dict['week_start'],
	            week_dict['week_end'])


def get_week_by_anydate(any_date):
	""" Returns a class Week """
	if not isinstance(any_date, dtdate):
		raise TypeError("Expected argument 'any_date' to be of type 'datetime.date'")

	date_dict = get_date_metadata(any_date)  # fetch from Redis
	if not date_dict:
		if frappe.db.get_single_value('Temporal Manager', 'debug_mode'):
			raise KeyError(f"WARNING: Unable to find Week in Redis for calendar date {any_date}.")
		return None
	return get_week_by_weeknum(date_dict['week_year'], date_dict['week_number'])


def get_weeks_as_dict(year, from_week_num, to_week_num):
	""" Given a range of Week numbers, return a List of dictionaries.

		From Shell: bench execute --args "2021,15,20" temporal.get_weeks_as_dict

	"""
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
		print(f"Processing week in year {year}")
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
# Other
# ----------------

def get_date_metadata(any_date):
	""" This function returns a date dictionary from Redis.

		bench execute --args "{'2021-04-18'}" temporal.get_date_metadata

	 """
	if isinstance(any_date, str):
		any_date = datetime.datetime.strptime(any_date, '%Y-%m-%d').date()
	if not isinstance(any_date, datetime.date):
		raise Exception(f"Argument 'any_date' should have type 'datetime.date', not '{type(any_date)}'")

	return temporal_redis.read_single_day(date_to_datekey(any_date))


def is_invalid_date_string(date_string):
	# dateutil parser does not agree with dates like "0001-01-01" or "0000-00-00"
	return (not date_string) or (date_string or "").startswith(("0001-01-01", "0000-00-00"))


def any_to_date(date_as_unknown):
	"""
	Given an argument of unknown Type, try to return a DateTime.
	"""
	try:
		if not date_as_unknown:
			return None
		if isinstance(date_as_unknown, str):
			return dateutil.parser.parse(date_as_unknown).date()
			# Alternately: return datetime.datetime.strptime(date_as_string,"%Y-%m-%d").date()
		if isinstance(date_as_unknown, datetime.date):
			return date_as_unknown

	except dateutil.parser._parser.ParserError:  # pylint: disable=protected-access
		frappe.throw(frappe._('{} is not a valid date string.')
		             .format(frappe.bold(date_as_unknown)),
		             title=frappe._('Invalid Date'))

	raise TypeError(f"Unhandled type ({type(date_as_unknown)}) for argument to function any_to_date()")


def datestr_to_date(date_as_string):
	"""
	Converts string date (yyyy-mm-dd) to datetime.date object.
	"""

	# ERPNext is very inconsistent with Date typing.  We should handle several possibilities:
	if not date_as_string:
		return None
	if isinstance(date_as_string, datetime.date):
		return date_as_string
	if not isinstance(date_as_string, str):
		raise TypeError(f"Argument 'date_as_string' should be of type String, not '{type(date_as_string)}'")
	if is_invalid_date_string(date_as_string):
		return None

	try:
		# Explicit is Better than Implicit.  The format should be YYYY-MM-DD.
		return dateutil.parser.parse(date_as_string, yearfirst=True, dayfirst=False).date()
		# Here's another way of doing the same thing:
		#     return datetime.datetime.strptime(date_as_string,"%Y-%m-%d").date()
	except dateutil.parser._parser.ParserError:  # pylint: disable=protected-access
		frappe.throw(frappe._('{} is not a valid date string.')
		             .format(frappe.bold(date_as_string)),
		             title=frappe._('Invalid Date'))

def timestr_to_time(time_as_string):
	"""
	Converts string time (8:30pm) to datetime.time object.
	"""

	"""
	8pm
	830pm
	830 pm
	8:30pm
	20:30
	8:30 pm
	"""


def date_to_sql_string(any_date):
	"""
	Given a date, create a String that MariaDB understands for queries (YYYY-MM-DD)
	"""
	if not isinstance(any_date, datetime.date):
		raise Exception(f"Argument 'any_date' should have type 'datetime.date', not '{type(any_date)}'")
	return any_date.strftime("%Y-%m-%d")

def get_earliest_date(list_of_dates):
	if not all(isinstance(x, datetime.date) for x in list_of_dates):
		raise ValueError("All values in argument must be datetime dates.")
	return min(list_of_dates)

def get_latest_date(list_of_dates):
	if not all(isinstance(x, datetime.date) for x in list_of_dates):
		raise ValueError("All values in argument must be datetime dates.")
	return max(list_of_dates)

# ----------------
# Weekdays
# ----------------

def weekday_string_to_shortname(weekday_string):
	"""
	Given a weekday name (MON, Monday, MONDAY), convert it to the short name.
	"""
	if weekday_string.upper() in (day['name_short'] for day in WEEKDAYS):
		return weekday_string.upper()

	ret = next(day['name_short'] for day in WEEKDAYS if day['name_long'].upper() == weekday_string.upper())
	return ret


def weekday_int_from_name(weekday_name, first_day_of_week='SUN'):
	"""
	Return the position of a Weekday in a Week.
	"""
	weekday_short_name = weekday_string_to_shortname(weekday_name)
	if first_day_of_week == 'SUN':
		result = next(weekday['pos'] for weekday in WEEKDAYS_SUN0 if weekday['name_short'] == weekday_short_name)
	elif first_day_of_week == 'MON':
		result = next(weekday['pos'] for weekday in WEEKDAYS_MON0 if weekday['name_short'] == weekday_short_name)
	else:
		raise Exception("Invalid first day of week (expected SUN or MON)")
	return result


def next_weekday_after_date(weekday, any_date):
	weekday_int = None
	if isinstance(weekday, int):
		weekday_int = weekday
	elif isinstance(weekday, str):
		weekday_int = weekday_int_from_name(weekday, first_day_of_week='MON')  # Monday-based math below

	days_ahead = weekday_int - any_date.weekday()
	if days_ahead <= 0:  # Target day already happened this week
		days_ahead += 7
	return any_date + datetime.timedelta(days_ahead)
