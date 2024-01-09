""" temporal/core.py """

# No internal dependencies allowed here.
import sys
from datetime import datetime

if sys.version_info.minor < 9:
	import pytz  # https://pypi.org/project/pytz/
	from dateutil.tz import tzutc
else:
	from zoneinfo import ZoneInfo

import frappe  # pylint: disable=wrong-import-position

if sys.version_info.major != 3:
	raise RuntimeError("Temporal is only available for Python 3.")


def is_datetime_naive(any_datetime):
	"""
	Returns True if the datetime is missing a Time Zone component.
	"""
	if not isinstance(any_datetime, datetime):
		raise TypeError("Argument 'any_datetime' must be a Python datetime object.")

	if any_datetime.tzinfo is None:
		return True
	return False


def get_system_timezone():
	"""
	Returns the Time Zone of the Site.
	"""
	system_time_zone = frappe.db.get_system_setting('time_zone')
	if not system_time_zone:
		raise RuntimeError("Please configure a Time Zone under 'System Settings'.")

	# Python 3.8 or less:
	if sys.version_info.minor < 9:
		return pytz.timezone(system_time_zone)
	# Python 3.9 or greater
	return ZoneInfo(system_time_zone)


def get_system_datetime_now():
	if sys.version_info.minor < 9:
		# Python 3.8 or less:
		utc_datetime = datetime.now(tzutc())  # Get the current UTC datetime.
	else:
		# Python 3.9 or greater
		utc_datetime = datetime.now(ZoneInfo("UTC"))  # Get the current UTC datetime.
	return utc_datetime.astimezone( get_system_timezone())  # Convert to the site's Time Zone:


def get_system_date():
	return get_system_datetime_now().date()


def datetime_to_sql_datetime(any_datetime: datetime):
	"""
	Convert a Python DateTime into a DateTime that can be written to MariaDB/MySQL.
	"""
	return any_datetime.strftime('%Y-%m-%d %H:%M:%S')


def make_datetime_naive(any_datetime):
	"""
	Takes a timezone-aware datetime, and makes it naive.
	Useful because Frappe is not storing timezone-aware datetimes in MySQL.
	"""
	return any_datetime.replace(tzinfo=None)


def make_datetime_tz_aware(naive_datetime):
	"""
	Add the ERP system time zone to any naive datetime.
	"""
	if naive_datetime.tzinfo:
		raise ValueError("Datetime is already localized and time zone aware.")

	return naive_datetime.replace(tzinfo=get_system_timezone())


def safeset(any_dict, key, value, as_value=False):
	"""
	This function is used for setting values on an existing Object, while respecting current keys.
	"""

	if not hasattr(any_dict, key):
		raise AttributeError(f"Cannot assign value to unknown attribute '{key}' in dictionary {any_dict}.")
	if isinstance(value, list) and not as_value:
		any_dict.__dict__[key] = []
		any_dict.extend(key, value)
	else:
		any_dict.__dict__[key] = value
