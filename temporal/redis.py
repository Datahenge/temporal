""" temporal/temporal/redis.py """

# ----------------
# Redis Functions
# ----------------

# Standard Library
from pprint import pprint

# Third Party
from six import iteritems

# Frappe
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
	year_key = f"temporal/year/{year_dict['year']}"
	cache().delete_key(year_key)
	for key,value in year_dict.items():
		cache().hset(year_key, key, value)
	if verbose:
		print(f"\u2713 Created temporal year '{year_key}' in Redis.")
		# pprint(read_single_year(year_dict['year']), depth=6)


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
	week_number_as_string = str(week_dict['week_number']).zfill(2)
	week_key = f"temporal/week/{week_dict['year']}-{week_number_as_string}"
	cache().delete_key(week_key)

	for key,value in week_dict.items():
		cache().hset(week_key, key, value)
	if verbose:
		print("Created a Temporal Week '{week_key}' in Redis:\n")
		pprint(read_single_week(week_dict[week_key]), depth=6)


def write_single_day(day_dict):
	""" Store a Day in Redis as a hash. """
	if not isinstance(day_dict, dict):
		raise TypeError("Argument 'day_dict' should be a Python Dictionary.")

	# For rationality, key format will be YYYY-MM-DD
	date_as_string = day_dict['date'].strftime("%Y-%m-%d")
	day_key = f"temporal/day/{date_as_string}"
	cache().delete_key(day_key)

	for key,value in day_dict.items():
		if key == 'date':
			# No point storing datetime.date; just store a sortable date string: YYYY-MM-DD
			cache().hset(day_key, key, date_as_string)
		else:
			cache().hset(day_key, key, value)

# ------------
# READING FROM REDIS
# ------------

def read_years():
	""" Returns a Python Tuple containing year integers. """
	year_tuple = tuple( int(year) for year in cache().smembers('temporal/years') )
	return sorted(year_tuple)  # redis does not naturally store Sets as sorted.


def read_single_year(year):
	""" Returns a Python Dictionary containing year-by-year data. """
	redis_hash =  cache().hgetall(f"temporal/year/{year}")
	if not redis_hash:
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
		return None
	return redis_hash_to_dict(redis_hash)


def read_weeks():
	""" Returns a Python Tuple containing Week Keys. """
	week_tuple = tuple( week for week in cache().smembers('temporal/weeks') )
	return sorted(week_tuple)  # redis does not naturally store Sets as sorted.


def read_single_week(week_key):
	""" Returns a Python Dictionary containing a Single Week. """
	redis_hash =  cache().hgetall(f"temporal/week/{week_key}")
	if not redis_hash:
		return None
	return redis_hash_to_dict(redis_hash)
