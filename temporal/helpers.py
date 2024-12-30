""" temporal.helpers.py """

import copy
from datetime import date as DateType
from temporal import date_to_iso_string

NoneType = type(None)

def dict_to_dateless_dict(some_object, replace_nones=False):
	"""
	Given an common object, convert any Dates to ISO Strings.
	"""
	result = copy.deepcopy(some_object)  # making a deep copy to be safe.

	# Scenario 1: Object is a Date
	if isinstance(result, DateType):
		return date_to_iso_string(some_object)

	# Scenario 1B: Object is a NoneType
	if replace_nones and isinstance(result, NoneType):
		return ""

	# Scenario 2: Object is a List
	if isinstance(some_object, list):
		return [dict_to_dateless_dict(v, replace_nones=replace_nones) for v in some_object]  # recursive call to this function.

	# Scenario 3: Argument is a Dictionary
	if isinstance(some_object, dict):
		new_dict = {}
		for key, value in some_object.items():
			new_dict[ key ] = dict_to_dateless_dict(value, replace_nones=replace_nones)  # recursive call to this function.
		return new_dict

	# Scenario 4: Argument is something not covered above (e.g. Integers)
	return some_object
