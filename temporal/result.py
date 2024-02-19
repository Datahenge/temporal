""" temporal.result """
# Extending what Python can return from a function call.

from enum import Enum
import json
from typing import NamedTuple

from temporal import validate_datatype
from temporal.helpers import dict_to_dateless_dict

PERFORM_TYPE_CHECKING = True


class FriendlyException(Exception):
	"""
	Python exceptions with optional, customer-facing messages.

	Usage:
		ex = FriendlyException("Friendly Message", "Internal-Only Message")
	"""
	def __init__(self, friendly_message, internal_message=None):

		self.friendly = friendly_message
		self.internal = internal_message or friendly_message
		super().__init__(self.internal)

	def __str__(self):
		return f"{self.args[0]}"

	def __friendly__(self):
		return self.friendly


# ========
# Define a Message
# ========

# NOTE: Define enum classes as both (str, Enum), so they are JSON serializable.

class MessageLevel(str, Enum):
	INFO = 'Info'
	WARNING = 'Warning'
	ERROR = 'Error'

class MessageAudience(str, Enum):
	ALL = 'All'
	INTERNAL = 'Internal'
	CUSTOMER = 'External'

class ResultMessage(NamedTuple):
	audience: MessageAudience
	message_level: MessageLevel
	message: str
	message_tags: list  # just a flexible attribute, useful for things like taggging messages as 'header-error' or 'line-error'

	@staticmethod
	def new(audience: MessageAudience, level: MessageLevel, message_string: str, tags: list=None):
		"""
		Create a new ResultMessageString
		"""
		if isinstance(tags, str):
			tags = [ tags ]
		return ResultMessage(
			audience=audience,
			message_level=level,
			message=message_string,
			message_tags=tags or []
		)

	def has_tag(self, message_tag) -> bool:
		return message_tag in self.message_tags

	def __str__(self):
		return f"{self.message_level} : {self.message}"

class OutcomeType(str, Enum):
	SUCCESS = 'Success'
	PARTIAL = 'Partial Success'  # For example, success with Warnings, dropped Order Lines.
	ERROR = 'Error'
	INTERNAL_ERROR = 'Runtime Error'  # unhandled Exceptions
	NONE = "None"  # used when something hasn't happened yet


class ResultBase():
	"""
	Extensible class for operations with Results and Related Data
	Examples include is base class with specific ones (Change Order Date, Un-Skip, Un-Pause, Cart Merging, Anon Registration)
	"""
	def __init__(self, validate_types=True, validate_schemas=True):

		self.outcome: OutcomeType = OutcomeType.SUCCESS
		self._messages = []
		self._data: dict = {}

		self._should_raise_exceptions = False  # should the consumer of this Result throw a Python Exception?
		self.runtime_exception = None

		self.validate_types = bool(validate_types)
		self.validate_schemas = bool(validate_schemas)

	def get_data(self, key=None):
		"""
		Return the data dictionary of the ResultBase class instance.
		"""
		if PERFORM_TYPE_CHECKING:
			validate_datatype("_data", self._data, dict, False)
		if not key:
			return self._data
		return self._data[key]

	def add_data(self, key, value):
		self._data[key] = value

	def append_data(self, key, value):
		if not isinstance(self._data[key], (list,set)):
			raise TypeError(f"ResultBase data element '{key}' is not a Python list or set.")
		self._data[key].append(value)

	def __bool__(self) -> bool:
		"""
		A useful overload.  For example: 'if Result():'
		"""
		if self.runtime_exception:
			return False
		return (self.outcome not in {OutcomeType.ERROR, OutcomeType.INTERNAL_ERROR})

	def as_dict(self) -> dict:
		return {
			"outcome": self.outcome,
			"data": dict_to_dateless_dict(self._data),
			"messages": dict_to_dateless_dict(self._messages)
		}

	def as_json(self):
		return json.dumps({
			"outcome": self.outcome,
			"data": dict_to_dateless_dict(self._data),
			"messages": dict_to_dateless_dict(self._messages)
		})

	def should_raise_exceptions(self) -> bool:
		if self.outcome in (OutcomeType.ERROR, OutcomeType.INTERNAL_ERROR):
			return True
		if self._should_raise_exceptions:
			return True
		if self.runtime_exception:
			return True
		return False

	# Message Functions
	def add_message(self, message):
		validate_datatype("message", message, ResultMessage, True)
		self._messages.append(message)

	def get_all_messages(self):
		return self._messages

	def get_error_messages(self):
		return [ each for each in self._messages if each.message_level == 'Error']  # MessageLevel.ERROR

	def get_warning_messages(self):
		return [ each for each in self._messages if each.message_level == 'Warning']  # MessageLevel.WARNING

	def get_info_messages(self):
		return [ each for each in self._messages if each.message_level == 'Info']  # MessageLevel.INFO

	def add_data_to_crs(self, crs_instance):
		"""
		Add this result's data to a Common Response Schmea for the FTP Middleware.
		"""
		converted_dict = dict_to_dateless_dict(self.get_data())  # NOTE: function already handles a deepcopy

		for key, value in converted_dict.items():
			crs_instance.add_data(key, value)  # important to send as JSON, to convert things like Date and DateTime to string.
