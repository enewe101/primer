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

EMAIL_LENGTH = 255
DEFAULT_TEXT_LENGTH = 32


class UserProfile(TimeStamped):
	user = models.OneToOneField(User, related_name='profile', 
		verbose_name=_('user'))
	email_validated = models.BooleanField(default=False, 
		verbose_name=_('email validated'))
	avatar_img = models.ImageField(upload_to='avatars', 
		verbose_name=_('avatar image'))


	class Meta:
		verbose_name = _('user profile')
		verbose_name_plural = _('user profiles')

                
	def __unicode__(self):
		return self.user.username


	def get_avatar_img_url(self):

		if self.avatar_img:
			return self.avatar_img.url

		else:
			return static('digidemo/images/avatar_not_found.png')



