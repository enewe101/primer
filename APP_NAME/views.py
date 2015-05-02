# -*- coding: utf-8 -*-
import collections as c
import pydenticon

from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext as __
from django.core import serializers
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.core.files import File
from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404, redirect
from django.template import Context, RequestContext
from django.template.loader import get_template
from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.forms.formsets import formset_factory
from django import http
from django.views.debug import ExceptionReporter
from django.conf import settings

from settings import DEBUG, TEMP_DIR
from APP_NAME.forms import *
from APP_NAME.shortcuts import send_email_confirmation, get_profile

import json
import sys


def get_globals(request):

	email_validated = True if ( 
			request.user.is_authenticated() 
			and get_profile(request.user).email_validated
		) else False

	#language_is_english = request.LANGUAGE_CODE.startswith('en')
	GLOBALS = {
		#'IS_ENGLISH': language_is_english,
		#'OTHER_LANG': 'fr' if language_is_english else 'en',
		'DEBUG': DEBUG,
		#'IN_PRODUCTION': IN_PRODUCTION,
		'IS_USER_AUTHENTICATED': request.user.is_authenticated(),
		#'IS_EMAIL_VALIDATED': email_validated,
		'USER': request.user,
		#'FEEDBACK_FORM': FeedbackForm(),
		'LOGIN_FORM': LoginForm(id_prefix='header')
	}    

    #if request.user.is_authenticated():
    #    # count how many were never seen before
    #    notifications = get_pretty_user_notifications(request.user) 
    #    unseen_notification_pks = [
    #        str(n.pk) for n in notifications if not n.was_seen]
    #    num_unseen = len(unseen_notification_pks)
    #    GLOBALS['NOTIFICATIONS'] = notifications
    #    GLOBALS['NUM_UNSEEN_NOTIFICATIONS'] = num_unseen
    #    GLOBALS['UNSEEN_NOTIFICATION_PKS'] = ','.join(
    #        unseen_notification_pks)

    #else:
    #    GLOBALS['NOTIFICATIONS'] = [] 
    #    GLOBALS['NUM_UNSEEN_NOTIFICATIONS'] = 0
    #    GLOBALS['UNSEEN_NOTIFICATION_PKS'] = '' 


	# nullifies notification behavior, delete this later
	GLOBALS['NOTIFICATIONS'] = [] 
	GLOBALS['NUM_UNSEEN_NOTIFICATIONS'] = 0
	GLOBALS['UNSEEN_NOTIFICATION_PKS'] = '' 

	return GLOBALS


def get_django_vars_JSON(additional_vars={}, request=None):
    return json.dumps(get_django_vars(
        request, additional_vars=additional_vars))


def get_django_vars(request, additional_vars={}):

    email_validated = True if (
            request.user.is_authenticated()
            and get_profile(request.user).email_validated
        ) else False

    django_vars = {
        'DEBUG': DEBUG,
        'IS_USER_AUTHENTICATED': request.user.is_authenticated(),
        'IS_EMAIL_VALIDATED': email_validated
    }

    django_vars.update(additional_vars)

    return django_vars


class AbstractView(object):

	# override this with desired template
	template = 'APP_NAME/__base.html'


	# Top-level request handler.
	# Give this function to the url resolver in urls.py.
	def view(self, request, *args, **kwargs):

		# Register the views arguments for easy access
		self.request = request
		self.args = args
		self.kwargs = kwargs

		# Delegate to a response handler
		if self.request.POST:
			return self.handle_post()

		else:
			return self.handle_get()


	# handles get requests.  Usually you don't need to override this.
	# Instead override to which it delegates
	def handle_get(self):
		# Create the response
		template = self.get_template()
		context = self.get_context()
		reply = HttpResponse(template.render(context))

		# Return the response
		return reply


	# This is hook makes it possible to do fancy template relolution.
	# But usually, a view should just override the `template` attribute.
	def get_template(self):
		return get_template(self.template)


	# Preloads the context with stuff that pretty much every view should have
	def get_default_context(self):

		return {
			'GLOBALS': get_globals(self.request),
			'django_vars_js': get_django_vars_JSON(request=self.request),
			'user': self.request.user
		}


	# Usually you should override get_context_data instead of this,
	# Which let's you keep the default context in tact.
	def get_context(self):
		context_data = self.get_default_context()
		context_data.update(self.get_context_data())
		return RequestContext(self.request, context_data)


	# Usually this is the only function to override.
	def get_context_data(self):
		raise NotImplementedError('Subclasses of AbstractView must override'
				+ ' get_context_data')

	
	# handles post requests.  Usually you'll want to override the functions
	# to which it delegates, rather than this itself.
	def handle_post(self):
		# Create the response
		template = self.get_template()
		context = self.get_post_context()
		reply = HttpResponse(template.render(context))

		# Return the response
		return reply


	# Usually you should override get_post_context_data instead of this,
	# which let's you keep the default context in tact.
	def get_post_context(self):
		context_data = self.get_default_context()
		context_data.update(self.get_post_context_data())
		return RequestContext(self.request, context_data)


	# This default makes POST requests handled like GET, unless overriden.
	def get_post_context_data(self):
		return self.get_context_data()



# This provides a base for creating views which only logged in users
# should be able to access.
#
# As an additional, optional protection, if this is a view which handles
# post data from a form that contains a `user` field, a check can be
# performed to ensure that the user indicated in the form is the same as the
# logged in user.  To perform this check, provide the class of the form
# in which a field called `user` occurs as the value for form_class.
# To opt out of this verification, set check_form_user = False.
#
class AbstractLoginRequiredView(AbstractView):

	form_class = None
	check_form_user = True

	def get_login_url(self, request):
		return reverse('login_required', kwargs={'next_url':request.path})

	def view(self, request, *args, **kwargs):

		if not request.user.is_authenticated():
			return redirect(self.get_login_url(request))

		elif not get_profile(request.user).email_validated:
			return redirect(reverse('invalid_email'))

		# if the form_class is set, we'll do an extra check when form data
		# has been posted, to make sure that the logged in user is the same
		# as the user in the form's user field.  If not, force a logout
		if request.POST and self.check_form_user is not None:

			# Make sure that we haven't just forgotten to set up the user
			# form validation.  This requires that check_user_form is
			# explicitly set to False in order to opt out of the check.
			if self.form_class is None:
				raise NotImplementedError(
					'AbstractLoginRequiredView could '\
					'not verify the form user field, because form_class was '\
					'None. Either provide a proper form_class, or set '\
					'check_form_user = False.'
				)

			form = self.form_class(request.POST)
			form.is_valid()
			if form.cleaned_data['user'] != request.user:
				force_logout(request)
				return redirect(self.get_login_url(request))

		return super(AbstractLoginRequiredView, self).view(
			request, *args, **kwargs)



class Index(AbstractView):

	template = 'APP_NAME/index.html'

	def get_context_data(self):
		return {}


def do_reload(request):
	return redirect(request.META['HTTP_REFERER'])



def resetPassword(request):
	if(request.method == 'POST'):
		pass_reset_form = ResetPasswordForm(
			request.POST,
			endpoint=reverse('resetPassword')
		)
		
		if pass_reset_form.is_valid():
			user = User.objects.get(
				username = pass_reset_form.cleaned_data['username'],
				email = pass_reset_form.cleaned_data['email']
			)
			new_password = str(uuid4()).replace('-', '')[:8]
			user.set_password(new_password)
			user.save()
			user.email_user(
				subject=_('Luminocracy.org Password Reset'),
				message=_('Your new luminocracy.org password is: %s')
					% new_password,
				from_email=_('support@luminocracy.org')
			)

			return index(request)

	else:
		pass_reset_form = ResetPasswordForm(endpoint=reverse('resetPassword'))
 
	return render(
		request,
		'APP_NAME/reset_password.html',
		{
			'GLOBALS': get_globals(request),
			'form' : pass_reset_form,
			'django_vars_js': get_django_vars_JSON(request=request)
		}
	)


class Login(AbstractView):
	template = 'APP_NAME/login_page.html'
	error = False


	# By default (if `next_url` is not set), send the user to the front page.
	#
	def view(self, *args, **kwargs):
		next_url = kwargs.pop('next_url', reverse('index'))
		return super(Login, self).view(*args, next_url=next_url, **kwargs)


	# Unauthenticated users get this page when accessing a login-required view
	def get_context_data(self):

		# Note, the request.path contains this login page url concatenated
		# with the original url they were trying to access
		login_form = LoginForm(endpoint=self.request.path)

		return {
			'GLOBALS': get_globals(self.request),
			'login_form': login_form,
			'error': self.error
		}


	# Handles displaying the empty form, ensures no error is printed
	def handle_get(self):
		self.error = False
		return super(Login,self).handle_get()


	# This handles the users login attempt
	def handle_post(self):

		login_success = login_user(
			self.request.POST['username'],
			self.request.POST['password'],
			self.request
		)

		if login_success == 'LOGIN_VALID_EMAIL':
			return redirect(self.kwargs['next_url'])

		elif login_success == 'LOGIN_INVALID_EMAIL':
			return redirect(reverse('invalid_email'))

		# Otherwise, show login form, but with an error message
		elif login_success == 'LOGIN_FAILED':
			self.error = True
			return super(Login, self).handle_get()



class InvalidEmail(AbstractView):
	template = 'APP_NAME/invalid_email.html'

	def get_context_data(self):
		return {}

		

def userRegistration(request):
	if(request.method == 'POST'):
		reg_form = UserRegisterForm(
			request.POST,
			endpoint=reverse('userRegistration')
		)
		
		# before validating the form, check if the email already exists
		# if so, we show the user an option to recover their credentials.
		try:
			email = request.POST['email']

		# if blank, forget about this check
		except KeyError:
			pass

		else:
			email_exists = User.objects.filter(email=email).count() > 0
			if email_exists:

				return render(
					request,
					'APP_NAME/register.html',
					{
						'GLOBALS': get_globals(request),
						'form': None,
						'email_exists': True, # changes how template displays
						'django_vars_js': get_django_vars_JSON(
							request=request)
					}
				)

		if reg_form.is_valid():

			new_user = User.objects.create_user(
				password = reg_form.cleaned_data['password'],
				username = reg_form.cleaned_data['username'],
				email = reg_form.cleaned_data['email'],
				first_name = reg_form.cleaned_data['first_name'],
				last_name = reg_form.cleaned_data['last_name']
			)

			user_profile = UserProfile(user=new_user)
			user_profile.save()

			# make a default avatar
			foreground = [ 
				"rgb(45,79,255)",
				"rgb(254,180,44)",
				"rgb(226,121,234)",
				"rgb(30,179,253)",
				"rgb(232,77,65)",
				"rgb(49,203,115)",
				"rgb(141,69,170)" 
			] 
			background = "rgb(224,224,224)"
			avatar_generator = pydenticon.Generator(
				8,8, foreground=foreground, background=background)
			avatar = avatar_generator.generate(
				new_user.username,240,240,output_format='png')

			img_dir = os.path.join(TEMP_DIR, '%s.png' % new_user.username)
			f = open(img_dir, 'wb')
			f.write(avatar)
			f.close()
			f = open(img_dir, 'r')
			user_profile.avatar_img.save(
				'%s.png' % new_user.username,
				File(f)
			)
			send_email_confirmation(new_user, request)
			return redirect(reverse('mail_sent'))

	else:
		reg_form = UserRegisterForm(
		endpoint=reverse('userRegistration'))

 
	return render(
		request,
		'APP_NAME/register.html',
		{
			'GLOBALS': get_globals(request),
			'form' : reg_form,
			'email_exists': False,
			'django_vars_js': get_django_vars_JSON(request=request)
		}
	)


def resend_email_confirmation(request):

		# only logged in users should be able to resend the verification email
		user = request.user
		if not user.is_authenticated():
			return HttpResponseForbidden()

		# only send the verification email if their email isn't validated
		if not get_profile(user).email_validated:
			send_email_confirmation(user, request)

		# Show the mail sent page
		return mail_sent(request)


def mail_sent(request):
	return render(
		request,
		'APP_NAME/check_your_mail.html',
		{
			'GLOBALS': get_globals(request),
			'django_vars_js': get_django_vars_JSON(request=request)
		}
	)


def verify_email(request, code):
	user = get_object_or_404(EmailVerification, code=code).user
	user_profile = get_profile(user)
	user_profile.email_validated = True
	user_profile.save()

	return render(
		request,
		'APP_NAME/validated.html',
		{
			'GLOBALS': get_globals(request),
			'django_vars_js': get_django_vars_JSON(request=request)
		}
	)
