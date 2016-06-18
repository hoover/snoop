DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'snoop',
    }
}

SECRET_KEY = 'some random secret key'

DEBUG = True
TIME_ZONE = 'Europe/Berlin'

MALDINI_ROOT = '/path/to/test/data'

ELASTICSEARCH_URL = 'http://localhost:9200'

TIKA_URL = 'http://localhost:9998'
TIKA_VERSION = '1.13'
TIKA_SERVER_ENDPOINT = TIKA_URL
TIKA_CLIENT_ONLY = True

MAX_TIKA_FILE_SIZE = 32 * (2 ** 20)  # 32mb