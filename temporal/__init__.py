# -*- coding: utf-8 -*-
from __future__ import unicode_literals

__version__ = '0.0.1'

""" temporal/temporal/__init__.py """

# Standard Library
import json
import datetime
from datetime import date
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
EPOCH_YEAR = 2020
END_YEAR = 2050

# Module Typing: https://docs.python.org/3.8/library/typing.html#module-typing

WEEKDAYS_SUN = ( 'SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT')
WEEKDAYS_MON = ( 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN')

class Week():
	""" A calendar week, starting on Sunday, where the week containing January 1st is always week #1 """
	def __init__(self, week_number, set_of_days, date_start, date_end):
		self.week_number = week_number
		self.set_of_days = set_of_days
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

	def build_years(self):
		""" Calculate years and write to Redis. """
		temporal_redis.write_years(self.years, verbose=self.verbose)
		for year in self.years:
			self.build_year(year)

	def build_year(self, year, verbose=False):
		date_start = date(year,1,1)
		date_end = date(year,12,31)
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
		start_date = date(self.epoch_year,1,1)  # could also do self.years[0]
		end_date = date(self.end_year, 12, 31)  # could also do self.years[-1]
		for date in range(start_date, end_date):
			print(f"Processing day {date}...")

	def build_weeks(self):
		""" Build all the weeks between Epoch Date and End Date """
		for year in self.years:
			self.build_week(year)

	def build_week(self, year):
		date_week_start = date(year, 1, 1)
		date_week_end = list(rrule(WEEKLY, byweekday=SA, dtstart=date(2021,1,1), until=date(2021,12,31)))[0]


class Internals():
	@staticmethod
	def date_to_week_number(any_date):
		""" Given a date, return the corresponding week number."""
		if not isinstance(any_date, datetime.date):
			raise TypeError("Argument must be of type 'datetime.date'")
		# Note: For weeks beginning with Sunday, use %V.
		# If we need weeks beginning with Monday, that's %U
		return int(any_date.strftime("%V"))

	@staticmethod
	def get_year_from_frappedate(frappe_date):
		return int(frappe_date[:4])

# ----------------
# Public Functions -->
# ----------------

def get_calendar_years():
	""" Fetch calendar years from Redis. """
	return temporal_redis.redis_get_calendar_years()

def get_calendar_year(year):
	return temporal_redis.redis_get_calendar_year(year)

def get_week_by_weeknum(week_number):
	""" Fetch a week from Redis, and build a Named Tuple 'Week' """

	week_start = datetime.strptime('2011 22 1', '%G %V %u')
	week_end = week_start + timedelta(days=6)
	return (week_number, week_start, week_end)

def get_week_by_anydate(anydate):
	""" Returns a named Tuple p = Namep = NamedTuple('Point', [('x', float), ('y', float)])dTuple('Point', [('x', float), ('y', float)])
	
	tuple of Week Number, Start Date, End Date. """

	p = NamedTuple('Point', [('x', float), ('y', float)])

	if not isinstance(as_of_date, datetime.date):
		raise TypeError("Expected argument 'as_of_date' to be of type 'datetime.date'")
	week_number = int(as_of_date.strftime("%V"))
	week_start = dt - timedelta(days=as_of_date.weekday())
	week_end = start + timedelta(days=6)
	return (week_number, week_start, week_end)


# -----------------
# Day Functions
# -----------------

def date_to_weekday_name(any_date):
	if not isinstance(any_date, datetime.date):
		raise TypeError("Argument 'any_date' should be a 'datetime.date'")
	return any_date.strftime('%A')

def date_to_weekday_position(any_date):
	if not any_date:
		raise ValueError("Argument 'any_date' is mandatory.")
	if not isinstance(any_date, datetime.date):
		raise TypeError("Argument 'any_date' should be a 'datetime.date'")
	return int(any_date.strftime('%w')) + 1
