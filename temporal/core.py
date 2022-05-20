""" temporal/core.py """

# No internal dependencies allowed here.
from datetime import datetime
from dateutil.tz import tzutc
import pytz

import frappe


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
		raise Exception("Please configure a Time Zone under 'System Settings'.")
	# This is for Python earlier than 3.9
	return pytz.timezone(system_time_zone)


def get_system_datetime_now():
	# This is for Python earlier than 3.9
	utc_datetime = datetime.now(tzutc())  # Get the current UTC datetime.
	return utc_datetime.astimezone( get_system_timezone())  # Convert to the site's Time Zone:


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
	if naive_datetime.tz_info:
		raise Exception("Datetime is already localized and time zone aware.")


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
