""" temporal.core """

# No internal dependencies allowed here.
from datetime import datetime
import pytz
import frappe


def get_system_timezone():
	"""
	Returns the Time Zone of the site.
	"""
	system_time_zone = frappe.db.get_system_setting('time_zone')
	if not system_time_zone:
		raise Exception("Please configure a Time Zone under 'System Settings'.")
	return pytz.timezone(system_time_zone)


def get_system_datetime_now():
	return datetime.now(get_system_timezone())  # Convert to the site's Time Zone:


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
	