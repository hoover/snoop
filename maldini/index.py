from django.conf import settings
import json
from elasticsearch import Elasticsearch
from . import models

es = Elasticsearch(settings.ELASTICSEARCH_URL)

def worker(id, verbose):
    try:
        digest = models.Digest.objects.get(id=id)
    except models.Digest.DoesNotExist:
        if verbose: print('MISSING')
        return

    digest_data = json.loads(digest.data)
    copy_keys = {
        'title',
        'path',
        'text',
        'subject',
        'date',
        'to',
        'from',
        'sha1',
        'md5',
        'lang',
        'date-created',
        'message-id',
        'in-reply-to',
        'thread-index',
        'references',
        'message',
    }

    data = {key: digest_data.get(key) for key in copy_keys}
    data['filetype'] = digest_data.get('type')
    data['attachments'] = bool(digest_data.get('attachments'))
    data['people'] = ' '.join([digest_data.get('from', '')] + digest_data.get('to', []))
    data['ocr'] = bool(digest_data.get('ocr'))
    data['ocrtext'] = digest_data.get('ocr')

    es.index(
        index=settings.ELASTICSEARCH_INDEX,
        doc_type='doc',
        id=digest.id,
        body=data,
    )
