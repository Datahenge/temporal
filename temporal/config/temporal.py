""" Define the menu for the App Module named 'Temporal' """

from frappe import _

def get_data():
	return [
		{
            "label": _("Basic"),
            "items": [
				{
					"type": "doctype",
					"name": "Temporal Manager",
					"description": _("Temporal Manager"),
					"onboard": 0,
				},
			]
		}
	]
