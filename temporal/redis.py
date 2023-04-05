""" temporal/temporal/redis.py """

# ----------------
# Redis Functions
# ----------------

# Standard Library
from pprint import pprint
import datetime

# Third Party
from six import iteritems

# Frappe
import frappe
from frappe import cache, msgprint, safe_decode

#  Redis Data Model:
#  I'm choosing to uses forward slash (/) to build Compound Keys

#  temporal/calyears		[ 2019, 2020, 2021]
#  temporal/calyear/2020	{ }

#  calyear:2020:weeks [ 1, 2, 3, 4, 5, ... ]
#  calyear:2020:wk1 : { 'firstday': '4/1/2020', lastday: '4/7/2020' }
#  calyear:2020:12:26 : { 'week' : 34 , 'dayname': Monday }


def redis_hash_to_dict(redis_hash, mandatory_arg=True):
	if not redis_hash:
		raise ValueError("Missing required argument 'redis_hash'")
	ret = {}
	for key, data in iteritems(redis_hash):
		key = safe_decode(key)
		ret[key] = data
	if mandatory_arg and (not ret):
		raise ValueError(f"Failed to create dictionary for Redis hash = {redis_hash}")
	return ret

# ---------------
# INTERNALS
# ---------------

def _year_to_yearkey(year):
	if not isinstance(year, int):
		raise TypeError("Argument 'year' should be a Python integer.")
	return f"temporal/year/{year}"

def _date_to_daykey(date):
	# For rationality, key format will be YYYY-MM-DD
	if not isinstance(date, datetime.date):
		raise TypeError("Argument 'date' should be a Python datetime Date.")
	date_as_string = date.strftime("%Y-%m-%d")
	day_key = f"temporal/day/{date_as_string}"
	return day_key

def _get_weekkey(year, week_number):
	""" Return a Redis weekkey """
	if not isinstance(week_number, int):
		week_number = int(week_number)
	if week_number > 53:
		raise ValueError("Week number must be an integer between 1 and 53.")
	if week_number < 1:
		raise ValueError("Week number must be an integer between 1 and 53.")
	week_number_str = str(week_number).zfill(2)
	return f"temporal/week/{year}-{week_number_str}"

# ------------
# WRITING TO REDIS
# ------------

def write_years(years_tuple, verbose=False):
	""" Create Redis list of Calendar Years. """
	if not isinstance(years_tuple, tuple):
		raise TypeError("Argument 'years_tuple' should be a Python Tuple.")
	cache().delete_key("temporal/years")
	for year in years_tuple:
		cache().sadd("temporal/years", year)  # add to set.
	if verbose:
		msgprint(f"Temporal Years: {read_years()}")


def write_single_year(year_dict, verbose=False):
	""" Store a year in Redis as a Hash. """
	if not isinstance(year_dict, dict):
		raise TypeError("Argument 'year_dict' should be a Python Dictionary.")
	year_key = _year_to_yearkey(int(year_dict['year']))
	cache().delete_key(year_key)
	for key,value in year_dict.items():
		cache().hset(year_key, key, value)
	if verbose:
		print(f"\u2713 Created temporal year '{year_key}' in Redis.")


def update_year(year, key, value, verbose=False):
	""" Update one of the hash values in the Redis Year. """
	# Example: Update the 'last_week_number' key, once Weeks have been generated.
	if not isinstance(year, int):
		raise TypeError("Argument 'year' should be a Python integer.")
	year_key = _year_to_yearkey(year)
	cache().hset(year_key, key, value)
	if verbose:
		pass

def write_weeks(weeks_tuple, verbose=False):
	""" Create Redis list of Weeks. """
	if not isinstance(weeks_tuple, tuple):
		raise TypeError("Argument 'weeks_tuple' should be a Python Tuple.")
	cache().delete_key("temporal/weeks")
	for week in weeks_tuple:
		cache().sadd("temporal/weeks", week)  # add to set.
	if verbose:
		msgprint(f"Temporal Weeks: {read_weeks()}")

def write_single_week(week_dict, verbose=False):
	""" Store a Week in Redis as a hash. """
	if not isinstance(week_dict, dict):
		raise TypeError("Argument 'week_dict' should be a Python Dictionary.")
	week_key = _get_weekkey(week_dict['year'], week_dict['week_number'])
	cache().delete_key(week_key)
	for key,value in week_dict.items():
		cache().hset(week_key, key, value)
	if verbose:
		print("Created a Temporal Week '{week_key}' in Redis:\n")
		pprint(read_single_week(week_dict['year'], week_dict['week_number']), depth=6)

def write_single_day(day_dict):
	""" 
	Store a Day in Redis as a hash.
	"""
	if not isinstance(day_dict, dict):
		raise TypeError("Argument 'day_dict' should be a Python Dictionary.")

	frappe.whatis(day_dict)

	hash_key = _date_to_daykey(day_dict['date'])
	cache().delete_key(hash_key)

	date_as_string = day_dict['date'].strftime("%Y-%m-%d")
	for key, value in day_dict.items():
		if key == 'date':
			# No point storing datetime.date; just store a sortable date string: YYYY-MM-DD
			cache().hset(hash_key, key, date_as_string)
		else:
			cache().hset(hash_key, key, value)

# ------------
# READING FROM REDIS
# ------------

def read_years():
	"""
	Returns a Python Tuple containing year integers.
	"""
	year_tuple = tuple( int(year) for year in cache().smembers('temporal/years') )
	return sorted(year_tuple)  # redis does not naturally store Sets as sorted.


def read_single_year(year):
	""" 
	Returns a Python Dictionary containing year-by-year data.
	"""
	year_key = _year_to_yearkey(year)
	redis_hash =  cache().hgetall(year_key)
	if not redis_hash:
		if frappe.db.get_single_value('Temporal Manager', 'debug_mode'):
			raise KeyError(f"Temporal was unable to find Redis key with name = {year_key}")
		return None
	return redis_hash_to_dict(redis_hash)


def read_days():
	""" Returns a Python Tuple containing Day Keys. """
	day_tuple = tuple( day_key for day_key in cache().smembers('temporal/days') )
	return sorted(day_tuple)  # Redis Sets are not stored in the Redis database.


def read_single_day(day_key):
	""" Returns a Python Dictionary containing a Single Day. """
	if not day_key.startswith('temporal'):
		raise ValueError("All Redis key arguments should begin with 'temporal'")
	redis_hash =  cache().hgetall(day_key)
	if not redis_hash:
		if frappe.db.get_single_value('Temporal Manager', 'debug_mode'):
			raise KeyError(f"Temporal was unable to find Redis key with name = {day_key}")
		return None
	return redis_hash_to_dict(redis_hash)


def read_weeks():
	""" Returns a Python Tuple containing Week Keys. """
	week_tuple = tuple( week for week in cache().smembers('temporal/weeks') )
	return sorted(week_tuple)  # redis does not naturally store Sets as sorted.


def read_single_week(year, week_number):
	""" Reads Redis, and returns a Python Dictionary containing a single Week. """
	week_key = _get_weekkey(year, week_number)
	redis_hash =  cache().hgetall(week_key)
	if not redis_hash:
		if frappe.db.get_single_value('Temporal Manager', 'debug_mode'):
			raise KeyError(f"Temporal was unable to find Redis key with name = {week_key}")
		return None
	return redis_hash_to_dict(redis_hash)
