from django.conf import settings
from django.db import transaction
import simplejson as json
from maldini import models
from dateutil import parser
import os
import tika
import tika.parser
import tika.language

tika.tika.TikaClientOnly = True


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
        'date_created':     _get_flat(meta, 'Creation-Date', 'dcterms:created', 'meta:created', 'created'),
        'date':             _get_flat(meta, 'Last-Modified', 'Last-Saved-Date', 'dcterms:modified',
                                      'meta:modified', 'created'),
        'encrypted-pdf':    _get_bool(meta, 'pdf:encrypted'),
        'tika':             meta
    }

    for key in ['date', 'date_created']:
        if key in data:
            data[key] = parser.parse(data[key]).isoformat()

    return data


@transaction.atomic
def tika_parse(sha1, buffer):
    cache, created = models.TikaCache.objects.get_or_create(sha1=sha1)
    if not created:
        return json.loads(cache.data)
    data = tika.parser.from_buffer(buffer, settings.TIKA_SERVER_ENDPOINT)
    cache.data = json.dumps(data)
    cache.save()
    return data

def tika_lang(sha1, buffer):
    # return tika.language.from_buffer(data['text'])
    pass
