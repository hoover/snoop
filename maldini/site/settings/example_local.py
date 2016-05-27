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
