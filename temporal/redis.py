# ----------------
# Redis Functions
# ----------------
from frappe import cache, msgprint, safe_decode
from six import iteritems
from pprint import pprint

#
#  Redis Data Model:
#  I'm choosing to uses forward slash (/) to build Compound Keys

#  temporal/calyears		[ 2019, 2020, 2021]
#  temporal/calyear/2020	{ }

#  calyear:2020:weeks [ 1, 2, 3, 4, 5, ... ]
#  calyear:2020:wk1 : { 'firstday': '4/1/2020', lastday: '4/7/2020' }
#  calyear:2020:12:26 : { 'week' : 34 , 'dayname': Monday }


"""
	doctype_map = cache.hget(cache_key, name)

	if doctype_map:
		# cached, return
		items = json.loads(doctype_map)

	cache = frappe.cache()
	cache_key = frappe.scrub(doctype) + '_map'

        cache.delete_value(key)
	cache.hset(cache_key, doctype, json.dumps(items))
"""

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


def write_years(years_tuple, verbose=False):
	""" Create Redis list of Calendar Years. """
	if not isinstance(years_tuple, tuple):
		raise TypeError("Argument 'year_set' should be a Python Set.")
	cache().delete_key("temporal/calyears")
	for year in years_tuple:
		cache().sadd("temporal/calyears", year)  # add to set.
	if verbose:
		msgprint(f"Calendar Years: {read_years()}")

def write_single_year(year_dict, verbose=False):
	""" Store a year in Redis as a Hash. """
	if not isinstance(year_dict, dict):
		raise TypeError("Argument 'year_dict' should be a Python Dictionary.")
	year_key = f"temporal/calyear/{year_dict['year']}"
	cache().delete_key(year_key)
	for key,value in year_dict.items():
		cache().hset(year_key, key, value)
	if verbose:
		print("Created calendar year '{year_key}' in Redis:\n")
		pprint(read_single_year(year_dict['year']), depth=6)

def write_weeks(verbose=False):
	""" Create weeks in Redis for each year since the epoch. """
	for year in get_calendar_years():
		if verbose:
			msgprint(f"Creating calendar weeks in Redis for year {year}")
		date_year_start = date(year, 1, 1)
		date_year_end = date(year, 12, 31)
		date_week_start = date(year, 1, 1)
		date_week_end = list(rrule(WEEKLY, byweekday=SA, dtstart=date(2021,1,1), until=date(2021,12,31)))[0]

def write_single_week(week_key, week_dict, verbose=False):
	cache().hset(week_key, "year", year)
	cache().hset(week_key, "date_start", startdate.strftime("%m/%d/%Y"))
	cache().hset(week_key, "date_end", enddate.strftime("%m/%d/%Y"))
	cache().hset(week_key, "days_in_year", days_in_year)

def read_years():
	""" Returns a Python Set containing year integers. """
	year_tuple = tuple( int(foo) for foo in cache().smembers('temporal/calyears') )
	return sorted(year_tuple)  # redis does not naturally store Sets as sorted.

def read_single_year(year):
	""" Returns a Python Dictionary containing year-by-year data. """
	redis_hash =  cache().hgetall(f"temporal/calyear/{year}")
	if not redis_hash:
		return None
	return redis_hash_to_dict(redis_hash)
