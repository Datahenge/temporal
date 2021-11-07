""" run_tests.py """


def test1():
	return "Foo"











	
"""
Test Case #1:
$ npx local-crontab  '0 10 * * *' --tz America/New_York
0 15 * 1-2,12 *
0 15 1-10 3 *
0 14 11-31 3 *
0 14 * 4-10 *
0 14 1-3 11 *
0 15 4-31 11 *

Test Case #2:
$ npx local-crontab  '0 10 * * *' --tz America/Denver
0 17 * 1-2,12 *
0 17 1-10 3 *
0 16 11-31 3 *
0 16 * 4-10 *
0 16 1-3 11 *
0 17 4-31 11 *
"""
