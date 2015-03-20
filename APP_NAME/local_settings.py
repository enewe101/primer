# These settings need to be eddited on new dev installations
PROJECT_DIR = '/Users/enewe101/projects/APP_NAME/APP_NAME'

# These settings don't normally need to be edited on new dev installations
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
		'NAME': 'APP_NAME',
		'USER': 'APP_NAME',
		'PASSWORD':'devpass',
		'HOST':'localhost'
    }
}
SECRET_KEY = 'dev_key_do_not_use_in_production__t7665_02i)odqry33bn3q$n_&7i8'
ALLOWED_HOSTS = ['localhost']
EMAIL_HOST_USER = "USER"
EMAIL_HOST_PASSWORD = "PASSWORD"
DEBUG = True
DEBUG_TEST = False
STRICT_TEMPLATE = True
DATA_FIXTURE = 'test_data'
IN_PRODUCTION = True
