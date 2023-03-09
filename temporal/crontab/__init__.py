""" __init__.py for module 'crontab' """

from datetime import datetime as datetimeType
import temporal


# TODO: Eventually this needs to migrate into the non-Frappe specific Temporal app I've created on GitLab
# However, that's going to require renaming *this* Temporal to frappe-temporal, and fixing all client environments.

# Dependencies:
# `pip install cron-converter`

def datetime_to_cron_string(any_datetime):
	return f"{any_datetime.minute} {any_datetime.hour} {any_datetime.day} {any_datetime.month} * {any_datetime.year}"

def date_and_time_to_cron_string(any_date, any_time):
	# Arguments might be strings, or datetime components.  Convert as needed.
	date_component = temporal.any_to_date(any_date)
	time_component = temporal.any_to_time(any_time)

	# Combine into a single datetime.
	my_datetime = datetimeType.combine(date_component, time_component)
	return datetime_to_cron_string(my_datetime)


def run_tests():
	from temporal.crontab import tests
	result = tests.test1()
	return result
