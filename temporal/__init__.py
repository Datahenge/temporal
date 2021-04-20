""" temporal/temporal/__init__.py """

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# Standard Library
import json
import datetime
from datetime import timedelta
from datetime import date as dtdate
from typing import Dict, Tuple, Sequence

# Third Party
import dateutil
from dateutil.rrule import rrule, WEEKLY
from dateutil.rrule import SU, MO, TU, WE, TH, FR, SA
from temporal import redis as temporal_redis  # alias to distinguish from Third Party module
# from six import iteritems

# Frappe modules.
import frappe
from frappe import _, throw, msgprint

# Constants
__version__ = '0.0.1'
EPOCH_YEAR = 2020
END_YEAR = 2050

# Module Typing: https://docs.python.org/3.8/library/typing.html#module-typing

WEEKDAYS_SUN = ( 'SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT')
WEEKDAYS_MON = ( 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN')

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

	def __init__(self, epoch_year=EPOCH_YEAR, end_year=END_YEAR, start_of_week='SUN', verbose=False):
		""" Initialize the Builder """
		if not isinstance(start_of_week, str):
			raise TypeError("Argument 'start_of_week' should be a Python String.")
		if start_of_week not in ('SUN', 'MON'):
			raise ValueError(f"Argument 'start of week' must be either 'SUN' or 'MON' (value passed was '{start_of_week}'")
		self.epoch_year = epoch_year
		self.end_year = end_year
		year_range = range(self.epoch_year, self.end_year + 1)  # because Python ranges are not inclusive
		self.years = tuple(year_range)
		self.weekdays = WEEKDAYS_SUN if start_of_week == 'SUN' else WEEKDAYS_MON
		self.verbose = verbose

	@staticmethod
	def build_all(epoch_year=EPOCH_YEAR, end_year=END_YEAR, start_of_week='SUN', verbose=False):
		instance = Builder(epoch_year=epoch_year, end_year=end_year,
		                   start_of_week=start_of_week, verbose=verbose)
		instance.build_years()
		instance.build_weeks()
		instance.build_days()

	def build_years(self):
		""" Calculate years and write to Redis. """
		temporal_redis.write_years(self.years, verbose=self.verbose)
		for year in self.years:
			self.build_year(year)

	def build_year(self, year):
		date_start = dtdate(year, 1, 1)
		date_end = dtdate(year,12,31)
		days_in_year = (date_end - date_start).days + 1
		jan_one_dayname = date_start.strftime("%a").upper()
		year_dict = {}
		year_dict['year'] = year
		year_dict['date_start'] = date_start.strftime("%m/%d/%Y")
		year_dict['date_end'] = date_end.strftime("%m/%d/%Y")
		year_dict['days_in_year'] = days_in_year
		# What day of the week is January 1st?
		year_dict['jan_one_dayname'] = jan_one_dayname
		year_dict['jan_one_weekpos'] = self.weekdays.index(jan_one_dayname) + 1  # because zero-based indexing
		temporal_redis.write_single_year(year_dict, self.verbose)

	def build_days(self):
		start_date = dtdate(self.epoch_year,1,1)  # could also do self.years[0]
		end_date = dtdate(self.end_year, 12, 31)  # could also do self.years[-1]

		count = 0
		for date_foo in Internals.date_range(start_date, end_date):
			day_dict = {}
			day_dict['date'] = date_foo
			day_dict['date_as_string'] = day_dict['date'].strftime("%Y-%m-%d")
			day_dict['weekday_name'] =  date_foo.strftime("%A")
			day_dict['weekday_name_short'] = date_foo.strftime("%a")
			day_dict['day_of_month'] =  date_foo.strftime("%d")
			day_dict['month_in_year_int'] = date_foo.strftime("%m")
			day_dict['month_in_year_str'] = date_foo.strftime("%B")
			day_dict['year'] = date_foo.year
			day_dict['day_of_year'] = date_foo.strftime("%j")
			if date_foo >= dtdate(year=date_foo.year, month=12, day=26):  # December 26th or later?
				day_dict['week_year'] = date_foo.year + 1
			else:
				day_dict['week_year'] = date_foo.year
			day_dict['week_number'] = Internals.date_to_week_number(date_foo)
			day_dict['index_in_week'] = int(date_foo.strftime("%w")) + 1  # 1-based indexing
			# Write this dictionary in the Redis cache:
			temporal_redis.write_single_day(day_dict)
			count += 1
		if self.verbose:
			print(f"\u2713 Created {count} Temporal Day keys in Redis.")

	def build_weeks(self):
		""" Build all the weeks between Epoch Date and End Date """
		# Begin on January 1st
		january_first = dtdate(self.epoch_year,1,1)
		january_index = int(january_first.strftime("%w"))

		week_start_date = january_first - timedelta(days=january_index)  # if January 1st is not Sunday, back up.
		week_end_date = None
		week_number = None

		print(f"Processing weeks starting with date: {week_start_date}")
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
			tuple_of_dates = tuple(list(Internals.date_range(week_start_date, week_end_date)))
			week_dict = {}
			week_dict['year'] = week_end_date.year
			week_dict['week_number'] = week_number
			week_dict['week_start'] = week_start_date
			week_dict['week_end'] = week_end_date
			week_dict['week_dates'] = tuple_of_dates
			temporal_redis.write_single_week(week_dict)
			# Increment to the Next Week
			week_start_date = week_start_date + timedelta(days=7)
			count += 1

		# Loop complete.
		if self.verbose:
			print(f"\u2713 Created {count} Temporal Week keys in Redis.")

class Internals():
	""" Internal functions that should not be called outside of Temporal. """
	@staticmethod
	def date_to_week_number(any_date):
		""" Given a date, return the corresponding week number.
			This uses a special calculation, that prevents "partial weeks"
		"""
		if not isinstance(any_date, datetime.date):
			raise TypeError("Argument must be of type 'datetime.date'")
		year_start_date = dtdate(any_date.year, 1, 1)

		year_start_pos_in_week = int(year_start_date.strftime("%w")) + 1
		date_pos_in_year = int(any_date.strftime("%j")) # e.g. April 1st is the 109th day in year 2020.
		# Formula
		# (( day_in_year - pos_of_Jan_1st ) / 7 ) + 1
		week_number = int((date_pos_in_year - year_start_pos_in_week) / 7 ) + 1
		return week_number

	@staticmethod
	def get_year_from_frappedate(frappe_date):
		return int(frappe_date[:4])

	@staticmethod
	def date_range(start_date, end_date):
		""" Generator for an inclusive range of dates.
		    It's pretty silly this isn't part of Python Standard Library or datetime
		"""
		# Important to add +1, otherwise the range is -not- inclusive.
		for number_of_days in range(int((end_date - start_date).days) + 1):
			yield start_date + timedelta(number_of_days)

# ----------------
# Public Functions
# ----------------

def get_calendar_years():
	""" Fetch calendar years from Redis. """
	return temporal_redis.read_years()

def get_calendar_year(year):
	""" Fetch a Year dictionary from Redis. """
	return temporal_redis.read_single_year(year)

def date_to_datekey(any_date):
	date_as_string = any_date.strftime("%Y-%m-%d")
	return f"temporal/day/{date_as_string}"

def week_to_weekkey(year, week_number):
	if not isinstance(week_number, int):
		raise TypeError("Argument 'week_number' should be a Python integer.")
	week_as_string = str(week_number).zfill(2)
	return f"temporal/week/{year}-{week_as_string}"

def get_date(any_date):
	""" Fetch a Day dictionary from Redis """
	return temporal_redis.read_single_day(date_to_datekey(any_date))

def get_week_by_weeknum(year, week_number):
	"""  Returns a class Week. """
	if not isinstance(week_number, int):
		raise TypeError("Argument 'week_number' must be an integer.")
	week_number_str = str(week_number).zfill(2)
	week_key = f"{year}-{week_number_str}"
	week_dict = temporal_redis.read_single_week(week_key)
	if not week_dict:
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
	date_dict = get_date(any_date)  # fetch from Redis
	if not date_dict:
		print(f"WARNING: Unable to find Week in Redis for calendar date {any_date}.")
		return None
	return get_week_by_weeknum(date_dict['week_year'], date_dict['week_number'])

def get_weeks_as_dict(year, from_week_num, to_week_num):
	""" Given a range of Week numbers, return a List of dictionaries. """
	from_week_num = int(from_week_num)
	to_week_num = int(to_week_num)

	weeks_list = []
	for week_num in range(from_week_num, to_week_num + 1):
		week_number_str = str(week_num).zfill(2)
		week_key = f"{year}-{week_number_str}"
		week_dict = temporal_redis.read_single_week(week_key)
		if week_dict:
			weeks_list.append(week_dict)
	return weeks_list
