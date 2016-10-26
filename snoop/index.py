from django.conf import settings
import json
from elasticsearch import Elasticsearch, helpers
from . import models
from .utils import worker_metrics

es = Elasticsearch(settings.SNOOP_ELASTICSEARCH_URL)

def get_index_data(digest_data):
    copy_keys = {
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
        'filename',
        'rev',
        'pgp',
        'word-count',
    }

    data = {key: digest_data.get(key) for key in copy_keys}
    data['filetype'] = digest_data.get('type')
    data['attachments'] = bool(digest_data.get('attachments'))
    data['people'] = ' '.join([digest_data.get('from', '')] + digest_data.get('to', []))
    data['ocr'] = bool(digest_data.get('ocr'))
    data['ocrtext'] = digest_data.get('ocr')

    return data

def worker(id, verbose):
    with worker_metrics(type='worker', queue='digest') as metrics:
        doc = models.Document.objects.get(id=id)
        metrics['document'] = doc.id
        metrics['index'] = doc.collection.es_index
        try:
            digest = models.Digest.objects.get(id=id)
        except models.Digest.DoesNotExist:
            if verbose: print('MISSING')
            metrics.update({'outcome': 'error', 'error': 'document_missing'})
            return

        digest_data = json.loads(digest.data)
        data = get_index_data(digest_data)

        es.index(
            index=doc.collection.es_index,
            doc_type='doc',
            id=digest.id,
            body=data,
        )

def bulk_worker(data_list, verbose):
    id_set = set(d['id'] for d in data_list)

    def iter_actions():
        for digest in models.Digest.objects.filter(id__in=id_set).iterator():
            index = models.Document.objects.get(id=digest.id).collection.index
            digest_data = json.loads(digest.data)
            data = get_index_data(digest_data)
            data.update({
                '_op_type': 'index',
                '_index': index,
                '_type': 'doc',
                '_id': digest.id,
            })
            yield data

    (ok, err) = helpers.bulk(es, stats_only=True, actions=iter_actions())
    if err:
        raise RuntimeError("Indexing failures: %d" % err)
