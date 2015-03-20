import logging
import os
import re

from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect
from django.template import Context
from django.template.loader import get_template
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext as __
from django.db import models
from django.forms import Form, ModelForm
from django import forms
from django.forms.formsets import formset_factory
from django.forms.models import modelformset_factory
from django.core.exceptions import ObjectDoesNotExist

from APP_NAME.models import *


USERNAME_MAX_LENGTH = 32
PASSWORD_MAX_LENGTH = 64
#USERNAME_MAX_LENGTH = 32
PASSWORD_MIN_LENGTH = 8

class AugmentedFormMixin(object):

	endpoint = None
	class_name = None

	def __init__(self, *args, **kwargs):

		# allow specifying the endpoint for the form.  This is the
		# form action ( <form action=... ), or ajax endpoint (ajax.py)
		self.endpoint = kwargs.pop('endpoint', self.endpoint)

		# The form gets a class name ( <form class=... )
		default_class_name = self.class_name or self.__class__.__name__
		self.form_class = kwargs.pop('form_class', default_class_name)

		# An id-prefix can optionally be specified.  This changes the
		# html id attribute form elements, but not the name attribute
		self.id_prefix = kwargs.pop('id_prefix', '')

		default_auto_id = self.form_class + '_' + str(self.id_prefix)

		# Customize the forms auto_id
		auto_id = kwargs.pop('auto_id', default_auto_id + '_%s')

		# The form's fields automatically get classes too, based on
		# the forms class and the fields name
		auto_add_input_class(self.form_class, self)

		# now call the usual form constructor
		super(AugmentedFormMixin, self).__init__(
			*args, auto_id=auto_id, **kwargs)


	def get_endpoint(self):
		# if none is supplied, theres no default, so an endpoint
		# *must be provided
		if self.endpoint is None:
			raise ValueError("No endpoint is bound to this form")

		return self.endpoint


	def json_errors(self):

		# We're going to make a dict of all fields and their errors
		# it will be exaustive (empty lists appear for fields without
		# errors.  First, get an empty error dict with all fields:
		all_fields = dict([(field.name, []) for field in self])

		# Now we get the fields that actually have some errors
		error_dict = {}
		for field, error_list in self.errors.items():
			field_id = field
			# field_id = self[field].id_for_label
			error_dict[field_id] = list(error_list)

		# mix them together before returning
		all_fields.update(error_dict)
		return all_fields


class LoginForm(AugmentedFormMixin, Form):
	endpoint = 'ajax_login'
	username = forms.CharField(max_length=USERNAME_MAX_LENGTH,
		label=_('username'))
	password = forms.CharField(
		widget=forms.PasswordInput(), max_length=PASSWORD_MAX_LENGTH,
		label=_('password'))

	class Meta:
		fields = ['username', 'password']
		widgets = {
			'password': forms.PasswordInput()
		}



class UserRegisterForm(AugmentedFormMixin, ModelForm):
	confirm_password = forms.CharField(
		widget=forms.PasswordInput(), max_length=PASSWORD_MAX_LENGTH,
		label=_('Confirm password'))

	class Meta:
		model = User
		fields = [
				'first_name', 'last_name', 'username', 'email', 'password',
				'confirm_password'
			]
		widgets = {
			'first_name': forms.TextInput(),
			'last_name': forms.TextInput(),
			'username': forms.TextInput(),
			'email': forms.EmailInput(),
			'password': forms.PasswordInput(),
		}


	def clean(self):

		# standard error checking by super.clean.  This already prevents
		# empty fields and using a username that's already taken.
		cleaned = super(UserRegisterForm, self).clean()

		# check that the email isn't already being used
		try:
			email = cleaned['email']

		# if the email is blank, nevermind
		except KeyError:
			pass
		
		else:
			email_exists = User.objects.filter(email=email).count()>0
			if email_exists:
				self._errors['email'] = self.error_class(
					[_("Hmm... looks like you've signed up before...")]
				)
				del cleaned['email']

		# check that the username is valid
		try:
			username = cleaned['username']

		# if the username is blank, nevermind
		except KeyError:
			pass

		else:
			LEGAL_USERNAME = re.compile(r'^\w+$')
			illegal_username = LEGAL_USERNAME.search(username) is None
			if illegal_username:
				self._errors['username'] = self.error_class(
					[_("Please stick to letters, numbers, and underscore!")])
				del cleaned['username']

		# check that passwords are long enough and match
		try:
			pwd1 = cleaned['password']

		# If the password is blank, nevermind: already caught by super.clean()
		except KeyError:
			pass

		else:
			try:
				pwd2 = cleaned['confirm_password']

			# If pwd confirmation blank, nevermind: already caught by super
			except KeyError:
				pass

			else:
				pwd_too_short = len(pwd1) < PASSWORD_MIN_LENGTH
				pwd_no_match = pwd1 != pwd2

				if pwd_too_short:
					self._errors['password'] = self.error_class(
						[_("Password too short")])

				if pwd_no_match:
					if 'password' in self._errors:
						self._errors['password'].append(
							_("Passwords didn't match!"))
					else:
						self._errors['password'] = self.error_class(
							[_("Passwords didn't match!")])

				if pwd_no_match or pwd_too_short:
					del cleaned['password']
					del cleaned['confirm_password']

		return cleaned

class ResetPasswordForm(AugmentedFormMixin,ModelForm):
	class Meta:
		model = PasswordReset
		fields = ['username', 'email']
		widgets = {
			'username': forms.TextInput(),
			'email': forms.EmailInput(),
		}


	def clean(self):
		cleaned = super(ResetPasswordForm, self).clean()
		user_email_match = False
		try:
		    User.objects.get(username = cleaned['username'],email = cleaned['email'])
		    user_email_match = True
		except ObjectDoesNotExist:
		    user_email_match = False
		
		if not user_email_match:
		    self._errors['username'] = self.error_class([_("Username doesn't exist or email doesn't match.")])
		
		return cleaned




def auto_add_input_class(form_class_name, form_instance):
    ''' 
    Add an html class to the widget html for all the widgets listed in a
    form's Meta.widgets dictionary.

    The html class is made from the form's class and the widget's field name
    e.g. If a CommentForm has a widget for the field `body`, the widget
    html would look like:
        <textarea class="CommentForm_body" ...

    '''
    for field in form_instance.Meta.fields:

        # for each field, get the widget
        try:
            attrs = form_instance.Meta.widgets[field].attrs
        except KeyError:
            continue

        # for each widget, get the html class attributed to it (if any)
        if 'class' in attrs:
            css_classes = attrs['class'] + ' ' 
        else:
            css_classes = ''

        # add an auto-generated class to the widget html's class
        if form_class_name not in css_classes:
            css_classes += form_class_name + '_' + field
            attrs['class'] = css_classes


class ProofRequestForm(AugmentedFormMixin, ModelForm):
	endpoint = '/request_proof/'
	class Meta:
		model = ProofRequest
		fields = ['text']
		widgets = {
			'text': forms.Textarea()
		}


