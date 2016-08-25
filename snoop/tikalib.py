from django.conf import settings
from . import models
from dateutil import parser
import os
import tika
import tika.parser
import tika.language
import hashlib

tika.tika.TikaClientOnly = True
tika.language.ServerEndpoint = settings.SNOOP_TIKA_SERVER_ENDPOINT


def extract_meta(meta):
    def _get_flat(dict, *keys):
        """
        Select the first non-null item from the dict that matches a key.
        If it's a list, take the first element from it.
        """
        item = None
        for key in keys:
            item = dict.get(key)
            if item is not None:
                break

        if type(item) is list:
            return item[0]

        return item

    def _get_bool(dict, *keys):
        """
        Select the first non-null item from the dict that matches a key.
        Cast it to bool.
        """
        item = _get_flat(dict, *keys)

        if not item:
            return False  # check for None

        if type(item) is bool:
            return item  # check if it's already a bool
        return item.lower() == "true"

    data = {
        'content-type':     _get_flat(meta, 'Content-Type', 'content-type'),
        'author':           _get_flat(meta, 'Author', 'meta:author', 'creator'),
        'date-created':     _get_flat(meta, 'Creation-Date', 'dcterms:created', 'meta:created', 'created'),
        'date':             _get_flat(meta, 'Last-Modified', 'Last-Saved-Date', 'dcterms:modified',
                                      'meta:modified', 'created'),
        'encrypted-pdf':    _get_bool(meta, 'pdf:encrypted'),
        'tika':             meta
    }

    for key in ['date', 'date-created']:
        if data.get(key):
            data[key] = parser.parse(data[key]).isoformat()

    return data


@models.cache(models.TikaCache, lambda sha1, open_file: sha1)
def tika_parse(sha1, open_file):
    with open_file() as f:
        return tika.parser.from_buffer(f, settings.SNOOP_TIKA_SERVER_ENDPOINT)

@models.cache(models.TikaLangCache,
    lambda text: hashlib.sha1(text.encode('utf-8')).hexdigest())
def tika_lang(text):
    lang = tika.language.from_buffer(text)
    if 'error' in lang.lower():
        raise RuntimeError("Unexpected error in tika language: %s" % sha1)
    return lang
