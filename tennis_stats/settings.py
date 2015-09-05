# Django settings for tennis_stats project.
import os

DEBUG = True
from settings_local import *


TEMPLATE_DEBUG = DEBUG

PROJECT_ROOT = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..')

print PROJECT_ROOT

ADMINS = (

)

MANAGERS = ADMINS
ALLOWED_HOSTS = ['.tennis-bot.com',]
TIME_ZONE = 'America/Chicago'
LANGUAGE_CODE = 'en-us'
SITE_ID = 1
USE_I18N = True
USE_L10N = True
USE_TZ = True
MEDIA_ROOT = ''
MEDIA_URL = ''
STATIC_ROOT = ''
STATIC_URL = '/static/'

STATICFILES_DIRS = (
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

SECRET_KEY = '2imwzd(8ha$=f^b-_q1v@yzm_vn_bm5%4d8^!ot#50&xl$rvx+'

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'tennis_stats.urls'
WSGI_APPLICATION = 'tennis_stats.wsgi.application'

TEMPLATE_DIRS = (
    os.path.join(PROJECT_ROOT, 'templates')
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'tennis',
    'south',
)

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}


USER_AGENT = "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/28.0.1500.71 Chrome/29.0.1500.71 Safari/537.36"
ACCEPT = "text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5"
TENNIS_URL = "http://sports.williamhill.com/bet/en-gb/betlive/24"
TIMEOUT = 30
INFO_BASE_URL = "http://sports.williamhill.com/bir_xml?action=commentary&ev_id="
TENNIS_POINTS = [0, 15, 30, 40, 'A']
MATCH_BASE_URL = "http://sports.williamhill.com/bet/en-gb/betting/e/"
ATP_EVENTS_URL = "http://www.atpworldtour.com/Scores/Archive-Event-Calendar.aspx"
ITF_MEN_CALENDAR = "http://www.itftennis.com/procircuit/tournaments/men's-calendar.aspx?"
ITF_WOMEN_CALENDAR = "http://www.itftennis.com/procircuit/tournaments/women's-calendar.aspx?"
PHANTOM_BIN = '/opt/bin/phantomjs'

DATADIR_SUCCES_BASE = "/opt/test_data/matches"
DATADIR_ERROR_BASE = "/opt/test_data/errors"