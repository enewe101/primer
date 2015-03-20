# -*- coding: utf-8 -*-
import os
from datetime import date, timedelta
from django import template
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext as __
from APP_NAME.models import *
from APP_NAME.shortcuts import get_profile

register = template.Library()


@register.tag(name='change_lang')
def change_lang(parser, token):
	try:
		tag_name = token.split_contents()
	
	except ValueError:
		raise template.TemplateSyntaxError(
			"%r tag takes no arguments" % token.contents.split()[0]
		)

	return ChangeLangNode()


class ChangeLangNode(template.Node):
	'''
		Supports a template tag that is similar to "static", but it 
		inserts the langage code in front of the file name so that
		to serve localized resources.  The path given should be the path to 
		the resource but where the language code is missing.

		e.g. {% localize_static "/path/to/resource.jpg" %}
		becomes /static-dir/path/to/en-ca_resource.jpg
		if the viewer's language code is en-ca
	'''


	def __init__(self):
	    pass
	
	def render(self, context):

		# get name and codes for the language opposite the one currently displayed
		is_english = context['GLOBALS']['IS_ENGLISH']
		language_name = u'Français' if is_english else u'English'
		language_code = u'/fr-ca' if is_english else u'/en-ca'

		# remove the language code part of the url
		url_no_language = os.path.join(*context['request'].path.split('/')[2:])

		# tack on the opposite language code
		url_switch_language = os.path.join(language_code, url_no_language)

		# make the language-switching link
		link = u'<a href="%s">%s</a>' % (url_switch_language, language_name)

		return mark_safe(link)


@register.tag(name="localize_static")
def localize_image(parser, token):
	'''
		Supports a template tag that is similar to "static", but it 
		inserts the langage code in front of the file name so that
		to serve localized resources.  The path given should be the path to 
		the resource but where the language code is missing.

		e.g. {% localize_static "/path/to/resource.jpg" %}
		becomes /static-dir/path/to/en-ca_resource.jpg
		if the viewer's language code is en-ca
	'''

	try:
		tag_name, url = token.split_contents()

	except ValueError:
		raise template.TemplateSyntaxError(
			"%r tag requires an image url as its only argument" 
			% token.contents.split()[0]
	)


	return ImageUrlNode(url)


class ImageUrlNode(template.Node):
	'''
		Supports a template tag that is similar to "static", but it 
		inserts the langage code in front of the file name so that
		to serve localized resources.  The path given should be the path to 
		the resource but where the language code is missing.

		e.g. {% localize_static "/path/to/resource.jpg" %}
		becomes /static-dir/path/to/en-ca_resource.jpg
		if the viewer's language code is en-ca
	'''


	def __init__(self, url):
	    self.url = url
	
	def render(self, context):
		url = self.url
	
		# strip the quotes if the image url is enquoted
		double_quoted = url.startswith('"') and url.endswith('"')
		single_quoted = url.startswith("'") and url.endswith("'")
		if double_quoted or single_quoted:
			url = url[1:-1]
		
		# tag on the language code to the filename part of the resource
		language_code = context['request'].LANGUAGE_CODE
		base_name =  language_code + '_' + os.path.basename(url)
		dir_name = os.path.dirname(url)
		return static(os.path.join(dir_name,base_name))


@register.filter(name='login_tip')
def login_tip(request):
	if request.user.is_authenticated():
		if get_profile(request.user).email_validated:
			return ''
		else:
			msg = __('You need to validate your email!')
			return mark_safe('title="%s"' % msg)

	else:
		msg = __('You need to login!')
		return mark_safe('title="%s"' % msg)



