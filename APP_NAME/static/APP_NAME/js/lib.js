

///////////////////////////////	
//  						 //
//  csrf-protection for ajax //
//  						 //
///////////////////////////////	

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}



function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

function sameOrigin(url) {
    // test that a given url is a same-origin URL
    // url could be relative or scheme relative or absolute
    var host = document.location.host; // host + port
    var protocol = document.location.protocol;
    var sr_origin = '//' + host;
    var origin = protocol + sr_origin;
    // Allow absolute or scheme relative URLs to same origin
    return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
        (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
        // or any other URL that isn't scheme relative or absolute i.e relative.
        !(/^(\/\/|http:|https:).*/.test(url));
}

$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
            // Send the token to same-origin, relative URLs only.
            // Send the token only if the method warrants CSRF protection
            // Using the CSRFToken value acquired earlier
            xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
        }
    }
});


function alert_ajax_error(response, textStatus) { 

	// for responses with http error code
	if(response.status) {
		js_error(response.status + ': ' + response.responseText);

	// for http success but with application error code
	} else {
		js_error(response.msg);
	}
};


///////////////////////////////	
//  						 //
//  ajax convinience methods //
//  						 //
///////////////////////////////	

if(typeof ALERT_AJAX_ERRORS == 'undefined') {
	ALERT_AJAX_ERRORS = false;
}


// sends the plain js object `data` to the django ajax function `endpoint`
// and optionally fires `success` or `error` with the parsed JSON response.
function ajax(endpoint, data, handlers) {

	handlers = handlers || {};

	var error = handlers['error'] || alert_ajax_error;

	$.ajax({
		"url": handle_ajax_url + endpoint + '/',
		"data": data,
		"method":'POST',
		"dataType": 'json',
		"success": handlers['success'],
		"error": error
	});
}


// Serializes the form as name-value pairs in a JSON object, sends this to the 
// django ajax function `endpoint` and optionally fires `success` or `error` 
// with the parsed JSON response.
function ajaxForm(endpoint, form, handlers) {
	form_as_array = form.serializeArray();
	as_dict = dict(form_as_array);
	ajax(endpoint, as_dict, handlers);
}


// Helper to turn an array of objects [{'name':<name>, 'value':<val>},...]
// into a flat object {<name>:<val>, ...}
function dict(arr) {
	var dict = {}

	for(var i=0; i<arr.length; i++) {

		var name = arr[i]['name'];
		var val = arr[i]['value'];

		if(name in dict) {

			if($.isArray(dict[name])) {
				dict[name].push(val)

			} else {
				dict[name] = [dict[name], val];
			}

		} else {
			dict[name] = val;
		}
	}

	return dict;
}



//////////////////////
//  				//
//  widget manager  //
//  				//
//////////////////////

var widgets = {}

function register_widget(widget_id, widget, widget_class) {
	widgets[widget_id] = {
		'widget_id': widget_id,
		'widget_class': widget_class || '',
		'widget': widget	
	}
}

function register_form(form_id, endpoint, form_class, submit_id) {

	var form_widget = new FormWidget(
		form_id, endpoint, submit_id);

	register_widget(form_id, form_widget, form_class);

}



//////////////////////////
//  					//
//  generic FormWidget  //
//  					//
//////////////////////////

function FormWidget(form_id, endpoint, submit_id) {

	// get the html elements that were passed by id
	var submit_button = $('#' + submit_id);
	var form = $('#'+form_id);

	var events = ['before', 'success', 'error', 'after'];
	var hooks = make_page_hooks(this, events) 
	hooks.error = alert_ajax_error;

	// note this is public
	this.submit = $.proxy(
		function() {
			ajaxForm(
				endpoint,
				form,
				{
					'before': $.proxy(function(data) {
						hooks['before']();
					}, this),

					'success': $.proxy(function(data, textStatus, jqXHR) {
						if(data.success) {
							hooks['success'](data, textStatus, jqXHR);
							render_errors(data, form_id);
						} else {
							hooks['error'](data, textStatus);
							render_errors(data, form_id);
						}

					}, this),

					'error': $.proxy(function(data, textStatus, jqXHR) {
						hooks['error'](data, textStatus, jqXHR);
						render_errors(data, form_id);
					}, this),

					'after': $.proxy(function(data, textStatus, jqXHR) {
						hooks['after']();
					}, this)
				}
			);
		}, this
	);

	submit_button.click(this.submit);
}


function render_errors(data, form_id) {

	// Since errors were returned, iterate over the fields, and mark
	// those with errors using styling and error text
	for(field_id in data.errors) {

		// the special field "__all__" represents errors with the form
		// in general.  There is a special div for this
		if(field_id == '__all__') {
			all_errs = $('#' + form_id + '_errors')
			all_errs.text(data.errors[field_id].join('<br />'));
		}

		// All other errors are field-specific.  get the field
		// only the field name is passed.  Tack on the id_prefix
		full_field_id = form_id + '_' + field_id;

		field = $('#'+full_field_id);

		// Deal with all the errors
		if(data.errors[field_id].length) {

			// Check if the field is hidden.  If so, then it's our
			// fault
			if(field.attr('type') == 'hidden') {
				alert("Oops... there has been a javascript error and "
					+ "we don't have the codes to deal with it.  It "
					+ "might go away if you refresh your browser.");
				continue;

			// otherwise its bad form data (user's fault). Mark errors.
			} else {
				$('#'+full_field_id).addClass('error')
				$('#'+full_field_id+'_errors').text(
					data.errors[field_id].join('<br />'))
			}

		// make sure that any OK fields get their errors cleared
		} else {

			// (but for hidden fields, there's nothing to do)
			if(field.attr('type') == 'hidden') {
				continue;
			}

			console.log(full_field_id);
			$('#'+full_field_id+'_errors').text('');
			$('#'+full_field_id).removeClass('error');
		}
	}
}



//////////////////
//  			//
//   js utils	//
//  			//
//////////////////

function js_error(err_msg) {
	if(django.DEBUG){
		alert(err_msg);
	}
}


function noop() {
}

function add_noops(handlers, events) {
	handlers = handlers || {};
	for(var i=0; i<events.length; i++) {
		var e = events[i];
		handlers[e] = handlers[e] || noop;
	}
	return handlers;
}


function conditional_ajax_error(handlers) {
	handlers = handlers || {}
	var error = handlers['error'];
	if(!error && ALERT_AJAX_ERRORS) {
		handlers['error'] = alert_ajax_error;
	}
	return handlers;
}


function make_page_hooks(obj, events) {

	// collect an array of valid hooks and initialize them to noop
	var valid_hooks = []
	var hooks = {}

	for(var i=0; i<events.length; i++) {
		valid_hooks.push(events[i]);
		hooks[events[i]] = noop;
	}

	// make a public hook assignment function
	var that = obj;
	that.hook = $.proxy( 
		function(hookname, f) {
			// do some validation
			// ensure hookname is valid
			if(!(hookname in hooks)) {
				js_error('hook error: ' + hookname 
					+ ' is not a valid hookname');
				return
			}

			// ensure hook is a function
			if(typeof f != 'function') {
				js_error('hook error: hook must be a function.  Got: ' 
					+ f);
			}

			// everything ok, assign the hook
			hooks[hookname] = f;
		},
		that
	);

	return hooks;
}


//////////////////////////
//  					//
//  ToggleHidden widget	//
//  					//
//////////////////////////

function ToggleHidden(toggle_div, content_1, content_2, message_1, message_2) {

	// content_2, message_2, and message_1 are optional.  Coerce to null if 
	// they weren't provided
	if(typeof content_2 == 'undefined') {
		content_2 = null;
	} 
	if(typeof message_1 == 'undefined') {
		message_1 = null;
	}
	if(typeof message_2 == 'undefined') {
		message_2 = null;
	}

	// we need to provide two messages for the toggle_text to get changed
	var has_messages = (message_2 != null);

	// Private function to hide content_2. Prevents us having to keep checking
	// if content 2 exists
	var hide_2 = function() {
		if(content_2 != null) {
			content_2.css('display', 'none')
		}
	};

	// Private function to show content_2. Prevents us having to keep checking
	// if content 2 exists
	var show_2 = function() {
		if(content_2 != null) {
			content_2.css('display', 'block')
		}
	};

	// INITIALIZE STATE
	//
	// determine whether content_1 is already displayed.  
	// This determines the starting state of the toggler.
	// Note: if content_1 is hidden, we force the display of content_2,
	// and if content_1 is shown, we force the display of content_2
	var state = null;
	if(content_1.css('display') == 'block') {
		state = 'showing_1';
		hide_2();

	} else {
		state = 'hiding_1';
		show_2();
	}

	// create hooks support
	var hooks = make_page_hooks(this, ['on_show', 'on_hide']);

	// note, this is public
	this.toggle = function() {
		if(state == 'showing_1') {
			content_1.css('display', 'none');
			show_2();
			if(has_messages) {
				toggle_div.html(message_2);
			}
			state = 'hiding_1';
			hooks.on_hide();

		} else if(state == 'hiding_1') {
			content_1.css('display', 'block');
			hide_2();
			if(has_messages) {
				toggle_div.html(message_1);
			}
			state = 'showing_1';
			hooks.on_show();

		} else {
			js_error('ToggleHidden: unexpected state');
		}
	}

	// Makes toggler show.  Does nothing if already showing
	// note, this is public
	this.show = function() {
		if(state == 'hiding_1') {
			content_1.css('display', 'block');
			hide_2();
			if(has_messages) {
				toggle_div.html(message_1);
			}
			state = 'showing_1';
			hooks.on_show();
		}
	};

	// Makes toggler hide.  Does nothing if already hidden
	// note, this is public
	this.hide = function() {
		if(state == 'showing_1') {
			content_1.css('display', 'none');
			show_2();
			if(has_messages) {
				toggle_div.html(message_2);
			}
			state = 'hiding_1';
			hooks.on_hide();
		}
	};
	
	// register display toggling behavior to clickable element
	toggle_div.click(this.toggle);
}



