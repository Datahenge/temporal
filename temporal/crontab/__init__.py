""" __init__.py for module 'crontab' """

#
# Dependencies:
# `pip install cron-converter`


def run_tests():
	from temporal.crontab import tests
	result = tests.test1()
	return result
