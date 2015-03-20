import json
from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.template import Context, RequestContext
from django.template.loader import get_template
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext as __
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout

from APP_NAME.settings import DEBUG
from APP_NAME.shortcuts import login_user

# json responders should return a python dict
_json_responders = {}


class AjaxError(Exception):
	pass


# decorator to register ajax responder endpoints
def ajax_endpoint(f):
	_json_responders[f.__name__] = f
	return f


def ajax_endpoint_login_required(error_msg=None, form_class=None):
	'''
	Use this decorator for ajax functions that should only honour requests
	from a logged in user.  When a request is made without an authenticated
	user, a sytem-level error message as well as a user-facing error message
	are returned to the client.

	If the ajax request came from a widget based on `_w_ajax_form.html`,
	then the system error message will appear in an alert box (if the 
	site is in DEBUG mode), and the user-facing message will get inserted
	into the widget's form_errors div.

	You can change the default user-facing error message by passing a string
	to the decorator as the `error_msg` argument.

	Any form that has a user field in it needs an extra step of validation.
	Although the user has been authenticated, we need to make sure that the
	user in the form is the same as the authenticated user.  Otherwise a 
	user could impersonate another by altering the user field.  we cannot 
	rely on the field (alone) therefore, but it is implicitly used when 
	form.save() is called.

	To validate that the user in the user field is the same as the logged in
	user, simply pass the class of the form to the decorator, as the second
	argument.  E.g. if you are processing a QuestionCommentForm, then pass
	`QuestionCommentForm` to the decorator, and it will perform this extra 
	check.  

	You *MUST* do this if the form has a user field!

	Note: This decorator must be called with parens following its name:
		like this --> @ajax_endpoint_login_required()
	'''

	# if no error_msg was given, use this default
	if error_msg is None:
		error_msg = 'You must login first!'

	# This function performs the act of decorating
	def decorate(original_func):

		# this function wraps the original endpoint function.  
		# It fires instead when the original function is called
		def wrapped(request):

			# check that the user is logged in
			if not request.user.is_authenticated():
				return {
					'success':False,
					'msg': 'user did not authenticate',
					'errors': {'__all__': 
						[error_msg]}
				}

			elif not get_profile(request.user).email_validated:
				return {
					'success':False,
					'msg': 'user email not validated',
					'errors': {'__all__': 
						['You must validate your email first!']}
				}

			# if the decoration was passed a form, then verify that the 
			# logged in user, and the user who requested the form are the same
			if form_class is not None:
				form = form_class(request.POST)
				form.is_valid()
				form_user = form.cleaned_data['user']
				if form_user != request.user:
					force_logout(request) # this is not implemented yet!
					return {
						'success':False,
						'msg': 'authenticated user did not match the '
							'user that requested the form',
						'errors':{'__all__':
							['Sorry, your session has expired...']}
					}

			# Finally, do whatever the original function does
			return original_func(request)

		# register the wrapped version as an ajax endpoint
		_json_responders[original_func.__name__] = wrapped

		# return the wrapped version to this module's namepsace
		return wrapped

	# The error message and form class (if any) were bound the custom decorator
	return decorate


# entry point handling all incomming ajax requests, 
# the request will be dispatched to the endpoint identified as `view` 
def ajax(request, view='test', *args, **kwargs):

	# Get the handler, or return an error to the client
	try:
		handler = _json_responders[view]

	except KeyError, e:
		msg = screen_ajax_error(AjaxError('no endpoint named %s.'%view))
		return HttpResponse(content=msg, status=404, reason='Not Found')

	# process the request with the handler.	
	try:
		data = handler(request, *args, **kwargs)

	except Exception, e:
		return HttpResponse(content=screen_ajax_error(e), status=500, 
			reason= 'Internal Server Error')

	# render and return the HttpResponse
	data = json.dumps(data)
	return render(request, 'APP_NAME/ajax.html', {'json_data':data})


def screen_ajax_error(e):

	if DEBUG:
		err_msg = "%s: %s" %(type(e).__name__, e)

	else:
		err_msg = "error"

	return err_msg


def vote(vote_spec, request):

	existing_vote = get_or_none(vote_spec['model'],
		user=request.POST['user'], target=request.POST['target']) 

	if existing_vote is not None:
		existing_valence = existing_vote.valence
	else:
		existing_valence = 0

	vote_form = vote_spec['form'](request.POST, instance=existing_vote)

	if vote_form.is_valid():

		# make sure that the vote is not being cast by a user on her own
		# content!
		content_author = vote_form.cleaned_data['target'].user
		if(request.user == content_author):
			return {
				'success':False, 
				'msg': 'user cannot vote on own content',
				'errors': ["You can't vote on your own post!"]
			}

		# record that the user has voted on this target
		vote_form.save()

		# increment or decrement the target score and author's rep
		target = vote_form.cleaned_data['target']
		author = target.user.profile

		if existing_valence == 1:
			target.score -= 1
			author.undo_rep(vote_spec['up_event'])

		elif existing_valence == -1:
			target.score += 1
			author.undo_rep(vote_spec['dn_event'])

		if vote_form.cleaned_data['valence'] == 1:
			target.score += 1
			author.apply_rep(vote_spec['up_event'])

		elif vote_form.cleaned_data['valence'] == -1:
			target.score -= 1
			author.apply_rep(vote_spec['dn_event'])

		target.save()
		author.save()

		return {'success':True}

	return {
		'success': False,
		'msg': 'ajax.py: vote(): VoteForm was not valid'
	}



#####################
#					#
#  ajax endpoints	#
#					#
#####################

@ajax_endpoint
def ajax_login(request):

	# attempt to authenticate the user
	username = request.POST['username']
	password = request.POST['password']
	login_success = login_user(username, password, request)


	# successful login
	if login_success == 'LOGIN_VALID_EMAIL':
		return {'success':True, 'email_valid': True, 'username':username}

	# successful login but invalid email
	elif login_success == 'LOGIN_INVALID_EMAIL':
		return {'success':True, 'email_valid': False}

	# failed login
	else: # login_success == 'LOGIN_FAILED':
		return {'success':False, 'email_valid': False}



@ajax_endpoint
def ajax_logout(request):
	logout(request)
	return {'success':True}



@ajax_endpoint
def checkValidUserName(request):
		username_pass = request.POST['username'];
		try :
			available = User.objects.get(username=username_pass);
			available = False;

		except:
			available = True;

		return {'success':True, 'available': available}

