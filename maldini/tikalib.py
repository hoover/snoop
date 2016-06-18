from django.conf import settings
import os

os.putenv('TIKA_URL', settings.TIKA_URL)
os.putenv('TIKA_VERSION', settings.TIKA_VERSION)
os.putenv('TIKA_SERVER_ENDPOINT', settings.TIKA_SERVER_ENDPOINT)
os.putenv('TIKA_CLIENT_ONLY', "True")

import tika
import tika.parser
import tika.language

def _extract_meta(meta):
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

    return data


def run_tika(buffer):
    data = {}
    parsed = tika.parser.from_buffer(buffer)
    data['text'] = parsed['content'].strip()
    data['lang'] = tika.language.from_buffer(data['text'])
    data.update(_extract_meta(parsed['metadata']))

    return data