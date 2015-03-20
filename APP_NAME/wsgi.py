"""
WSGI config for APP_NAME project.
"""

import sys
import os

sys.path.append('/Users/enewe101/projects/APP_NAME/APP_NAME')
sys.path.append('/Library/Frameworks/EPD64.framework/Versions/7.3/lib/python2.7/site-packages')
sys.path.append('/Library/Frameworks/EPD64.framework/Versions/7.3/lib/python2.7/site-packages/MySQL_python-1.2.3-py2.7-macosx-10.5-x86_64.egg/')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "APP_NAME.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
