// Copyright (c) 2021, Datahenge LLC and contributors
// For license information, please see license.txt

frappe.ui.form.on('Temporal Manager', {
	refresh: function(frm) {

	},

	btn_show_weeks:  function(frm) {
		dialog_show_redis_weeks();
	}
});


function dialog_show_redis_weeks() {

	var mydialog = new frappe.ui.Dialog({
		title: 'Display Weeks from the Temporal Redis database',
		width: 100,
		fields: [
			{
				'fieldtype': 'Int',
				'label': __('Year'),
				'fieldname': 'year',
				'default': moment(new Date()).year()
			},
			{
				'fieldtype': 'Int',
				'label': __('From Week Number'),
				'fieldname': 'from_week_num',
				'default': 1
			},
			{
				'fieldtype': 'Int',
				'label': __('To Week Number'),
				'fieldname': 'to_week_num',
				'default': 52
			}
		]
	});

	mydialog.set_primary_action(__('Show'), args => {
		let foo = frappe.call({
			method: 'temporal.get_weeks_as_dict',
			// Arguments must precisely match the Python function declaration.
			args: { year: args.year, from_week_num: args.from_week_num, to_week_num: args.to_week_num },
			callback: function(r) {
				if (r.message) {
					let message_object = JSON.parse(r.message);
					//message_object.forEach(function (item, index) {
					//  console.log(item, index);
					// });
				}
			}
		});
		mydialog.hide();  // After callback, close dialog regardless of result.
	});

	// Now that we've defined it, show that dialog.
	mydialog.show();
};

