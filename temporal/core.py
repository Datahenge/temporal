""" temporal/core.py """
# pylint: disable=unused-import

# No internal dependencies allowed here.
import sys
# from datetime import datetime

# Third Party
import temporal_lib
from temporal_lib.core import (
	is_datetime_naive,
	localize_datetime,
	make_datetime_naive,
	TimeZone
)
from temporal_lib.tlib_date import (
	datetime_to_sql_datetime
)

# Frappe
import frappe

if sys.version_info.major != 3:
	raise RuntimeError("Temporal is only available for Python 3.")


def get_system_timezone():
	"""
	Returns the Time Zone of the Site.
	"""
	system_time_zone = frappe.db.get_system_setting('time_zone')
	if not system_time_zone:
		raise ValueError("Please configure a Time Zone under 'System Settings'.")
	return TimeZone(system_time_zone)


def get_system_datetime_now():
	"""
	Get the system datetime using the current time zone.
	"""
	return temporal_lib.core.get_system_datetime_now(get_system_timezone())


def get_system_date():
	return get_system_datetime_now().date()


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


def make_datetime_tz_aware(naive_datetime):
	"""
	Given a naive datetime, localize to the ERPNext system timezone.
	"""
	return localize_datetime(naive_datetime, get_system_timezone())
