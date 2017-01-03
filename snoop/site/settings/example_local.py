DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'hoover-snoop',
    }
}

DEBUG = True
SECRET_KEY = 'FIME: generate random string'

SNOOP_ROOT = '/path/to/test/data'

SNOOP_MSGCONVERT_SCRIPT = 'msgconvert'
SNOOP_MSG_CACHE = 'path/to/msg/cache'

SNOOP_ARCHIVE_CACHE_ROOT = '/path/to/archive/cache'
SNOOP_SEVENZIP_BINARY = '7z'

SNOOP_PST_CACHE_ROOT = '/path/to/pst/cache'
SNOOP_READPST_BINARY = 'readpst'

SNOOP_GPG_HOME = '/path/to/gpg/home'
SNOOP_GPG_BINARY = 'gpg'

SNOOP_LOG_DIR = '/path/to/log/dir'

SNOOP_TIKA_SERVER_ENDPOINT = 'http://localhost:9998/'
