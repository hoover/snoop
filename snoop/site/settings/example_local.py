DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'hoover-snoop',
    }
}

SECRET_KEY = 'some random secret key'

DEBUG = True
TIME_ZONE = 'Europe/Berlin'

SNOOP_ROOT = '/path/to/test/data'

ELASTICSEARCH_URL = 'http://localhost:9200'

TIKA_SERVER_ENDPOINT = 'http://localhost:9998'
TIKA_FILE_TYPES = ['doc', 'pdf', 'xls', 'ppt']
MAX_TIKA_FILE_SIZE = 32 * (2 ** 20)  # 32mb
MSGCONVERT_SCRIPT = 'msgconvert'
ARCHIVE_CACHE_ROOT = '/path/to/archive/cache'
SEVENZIP_BINARY = '7z'
ELASTICSEARCH_INDEX = 'hoover'

SNOOP_PST_CACHE_ROOT = '/path/to/pst/cache'
READPST_BINARY = 'readpst'

SNOOP_GPG_HOME = '/path/to/gpg/home'
SNOOP_GPG_BINARY = 'gpg'
