# Includes
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext as __
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify
from django.utils.safestring import mark_safe
from django.contrib.staticfiles.templatetags.staticfiles import static
from APP_NAME.abstract_models import TimeStamped
import os

MY_NUMBER = '1 450-977-1055'
EMAIL_LENGTH = 255
DEFAULT_TEXT_LENGTH = 32

class ProofRequest(TimeStamped):
	STATUS_CHOICES = [
		('posted', 'posted'),
		('improved', 'improved'),
		('retrieved', 'retrieved'),
		('deleted', 'deleted')
	]
	user = models.ForeignKey(User, verbose_name=_('user'))
	text = models.TextField()
	status = models.CharField(max_length=16, choices=STATUS_CHOICES)


class Proof(TimeStamped):
	user = models.ForeignKey(User, verbose_name=_('user'))
	text = models.TextField()


class PasswordReset(TimeStamped):
	'''
		This is for password reset
	'''
	email = models.EmailField(max_length=EMAIL_LENGTH, verbose_name=_('email'))
	username = models.CharField(max_length=DEFAULT_TEXT_LENGTH, 
		verbose_name=_('username'))

	class Meta:
		verbose_name = _('Password reset request')
		verbose_name_plural = _('Password reset requests')



class UserProfile(TimeStamped):
	user = models.OneToOneField(User, related_name='profile', 
		verbose_name=_('user'))
	email_validated = models.BooleanField(default=False, 
		verbose_name=_('email validated'))
	avatar_img = models.ImageField(upload_to='avatars', 
		verbose_name=_('avatar image'))
	rep = models.IntegerField(default=0, verbose_name=_('reputation'))
	do_email_news = models.BooleanField(default=True, 
		verbose_name=_('do email news'))
	do_email_responses = models.BooleanField(default=True, 
		verbose_name=_('do email responses'))
	do_email_petitions = models.BooleanField(default=True, 
		verbose_name=_('do email petitions'))
	do_email_watched = models.BooleanField(default=True, 
		verbose_name=_('do email watched'))

	class Meta:
		verbose_name = _('user profile')
		verbose_name_plural = _('user profiles')


	# non-field class attributes
	rep_events = {
		'up_proposal': 10,
		'dn_proposal': -2,
		'up_letter': 10,
		'dn_letter': -2,
		'do_downvote': -2,
		'up_comment': 5,
		'dn_comment': -2,
		'up_discussion': 10,
		'dn_discussion': -2,
		'up_question': 10,
		'dn_question': -2,
		'up_answer': 10,
		'dn_answer': -2,
		'up_reply': 10,
		'dn_reply': -2,
	}
                
	def __unicode__(self):
		return self.user.username


	def get_rep_delta(self, event_name):
		# Validation: event_name should be a string
		if not isinstance(event_name, basestring):
			raise ValueError('UserProfile.apply_score: event_name should'
				'be string-like.')

		try:
			rep_delta = self.rep_events[event_name]

		except KeyError as e:
			raise ValueError('UserProfile: there is no %s rep-event.' %
					str(event_name))

		return rep_delta


	def apply_rep(self, event_name):
		self.rep += self.get_rep_delta(event_name)


	def undo_rep(self, event_name):
		self.rep -= self.get_rep_delta(event_name)

	def get_user_url(self):
		url_stub = reverse('userProfile', kwargs={'userName': self.user.username})
		return url_stub;
	

	def get_avatar_img_url(self):

		if self.avatar_img:
			return self.avatar_img.url

		else:
			return static('digidemo/images/avatar_not_found.png')


class EmailVerification(TimeStamped):
	user = models.ForeignKey(User, verbose_name=_('user'))
	code = models.CharField(max_length=60, verbose_name=_('code'))

	class Meta:
		verbose_name = _('email verification')
		verbose_name_plural = _('email verifications')
