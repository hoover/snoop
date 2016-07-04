from maldini.site.settings.common import *

SECRET_KEY = 'fake-key'
MALDINI_CACHE = False
MALDINI_ANALYZE_LANG = False
TIKA_FILE_TYPES = []
TIKA_SERVER_ENDPOINT = None

from maldini.site.settings.testing_local import *
