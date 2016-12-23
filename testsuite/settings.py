from snoop.site.settings.common import *

SECRET_KEY = 'fake-key'
SNOOP_CACHE = False
SNOOP_ANALYZE_LANG = False
SNOOP_TIKA_FILE_TYPES = []
SNOOP_TIKA_SERVER_ENDPOINT = None
SNOOP_FEED_PAGE_SIZE = 10

from snoop.site.settings.testing_local import *
