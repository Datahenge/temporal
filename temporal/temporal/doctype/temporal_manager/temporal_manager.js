// Copyright (c) 2021, Datahenge LLC and contributors
// For license information, please see license.txt

frappe.ui.form.on('Temporal Manager', {
	refresh: function(frm) {

		// The code below allows for Python itself to trigger our dialog.
		frappe.realtime.on("Dialog Show Redis Weeks", () => {
			console.log("Caught 1 inside of JS.");
			dialog_show_redis_weeks();
		});
	}
});


$(document).on('app_ready', function () {
	frappe.realtime.on("Dialog Show Redis Weeks", () => {
		console.log("Caught 1 inside of JS.");
		dialog_show_redis_weeks();
	});
});


function dialog_show_redis_weeks() {

	console.log("Caught 2 inside of JS.");

	var mydialog = new frappe.ui.Dialog({
		title: 'Display Weeks from the Temporal Redis database',
		width: 100,
		fields: [
			{
				'fieldtype': 'Int',
				'label': __('Year'),
				'fieldname': 'year',
			},
			{
				'fieldtype': 'Int',
				'label': __('From Week Number'),
				'fieldname': 'from_week_num',
			},
			{
				'fieldtype': 'Int',
				'label': __('To Week Number'),
				'fieldname': 'to_week_num',
			}
		]
	});

	// TODO: Not thrilled with this solution, because the URL can become quite Long.
	mydialog.set_primary_action(__('Show'), args => {
		let foo = frappe.call({
			method: 'temporal.get_weeks_as_dict',
			// Arguments must precisely match the Python function declaration.
			args: { year: args.year, from_week_num: args.from_week_num, to_week_num: args.to_week_num },
			callback: function(r) {
				if (r.message) {
					frappe.message(r);
				}
			}
		});
		mydialog.hide();  // After callback, close dialog regardless of result.
	});

	// Now that we've defined it, show that dialog.
	mydialog.show();
};

