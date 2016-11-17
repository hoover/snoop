SNOOP_ROOT = '/path/to/testdata/data'

SNOOP_MSGCONVERT_SCRIPT = 'msgconvert'
SNOOP_SEVENZIP_BINARY = '7z'
SNOOP_READPST_BINARY = 'readpst'
SNOOP_GPG_BINARY = 'gpg'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'hoover-snoop',
    },
}
