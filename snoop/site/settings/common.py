import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'snoop',
]

MIDDLEWARE_CLASSES = [
]

ROOT_URLCONF = 'snoop.site.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.jinja2.Jinja2',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'environment': 'snoop.views.environment',
        },
    },
]

WSGI_APPLICATION = 'snoop.site.wsgi.application'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = False
USE_L10N = False
USE_TZ = True

STATIC_URL = '/static/'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'logfile': {
            'format': ('%(asctime)s %(process)d '
                       '%(levelname)s %(name)s %(message)s'),
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'loggers': {
        'django.request': {
            'level': 'WARNING',
            'propagate': False,
            'handlers': ['stderr'],
        },
        'snoop': {
            'level': 'INFO',
            'propagate': False,
            'handlers': ['stderr'],
        },
        '': {
            'level': 'WARNING',
            'propagate': True,
            'handlers': ['stderr'],
        },
    },
    'handlers': {
        'stderr': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'logfile',
        },
    },
}

SNOOP_CACHE = True

SNOOP_ELASTICSEARCH_URL = 'http://localhost:9200'
SNOOP_ELASTICSEARCH_INDEX = 'hoover'

SNOOP_ANALYZE_LANG = False
SNOOP_TIKA_MAX_FILE_SIZE = 50 * 1024 * 1024 # 50M
SNOOP_TIKA_FILE_TYPES = ['doc', 'pdf', 'xls', 'ppt']
SNOOP_TIKA_SERVER_ENDPOINT = 'http://localhost:9998/'

SNOOP_MSGCONVERT_SCRIPT = None
SNOOP_MSG_CACHE = None
SNOOP_FLAG_MSGCONVERT_FAIL = False

SNOOP_SEVENZIP_BINARY = None
SNOOP_ARCHIVE_CACHE_ROOT = None

SNOOP_PST_CACHE_ROOT = None
SNOOP_READPST_BINARY = None

SNOOP_GPG_HOME = None
SNOOP_GPG_BINARY = None

SNOOP_LOG_DIR = None
