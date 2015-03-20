from django.db import models
from django.contrib.auth.models import User
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.utils import timezone 
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify
import re
import os


# *** Abstract Models *** #

class TimeStamped(models.Model):
	creation_date = models.DateTimeField(editable=False, 
		verbose_name=_('creation date'))
	last_modified = models.DateTimeField(editable=False, 
		verbose_name=_('last modified'))

	def save(self, *args, **kwargs):
		if not self.creation_date:
			self.creation_date = timezone.now()
		
		self.last_modified = timezone.now()
		return super(TimeStamped, self).save(*args, **kwargs)

	class Meta:
		abstract = True

