from django.conf import settings
import simplejson as json
from elasticsearch import Elasticsearch
from maldini import models
from maldini import queues
from maldini import digest as digest_module
from maldini import emails

es = Elasticsearch(settings.ELASTICSEARCH_URL)

def digest(id, verbose):
    try:
        document = models.Document.objects.get(id=id)
    except models.Document.DoesNotExist:
        if verbose: print('MISSING')
        return

    try:
        data = digest_module.digest(document)

    except emails.MissingEmlxPart:
        document.broken = 'missing_emlx_part'
        document.save()
        if verbose: print('missing_emlx_part')
        return

    except emails.PayloadError:
        document.broken = 'payload_error'
        document.save()
        if verbose: print('payload_error')
        return

    except emails.CorruptedFile:
        document.broken = 'corrupted_file'
        document.save()
        if verbose: print('corrupted_file')
        return

    else:
        if document.broken:
            if verbose: print('removing broken flag', document.broken)
            document.broken = ''
            document.save()

    for name, info in data.get('attachments', {}).items():
        child, created = models.Document.objects.update_or_create(
            container=document,
            path=name,
            defaults={
                'disk_size': 0,
                'content_type': info['content_type'],
                'filename': info['filename'],
            },
        )

        if created:
            queues.put('digest', {'id': child.id}, verbose=verbose)
            if verbose: print('new child', child.id)

    models.Digest.objects.update_or_create(
        id=document.id,
        defaults={'data': json.dumps(data)},
    )

    queues.put('index', {'id': document.id}, verbose=verbose)

def index(id, verbose):
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
    }

    data = {key: digest_data.get(key) for key in copy_keys}
    data['filetype'] = digest_data.get('type')
    data['attachments'] = bool(digest_data.get('attachments'))
    data['people'] = ' '.join([digest_data.get('from', '')] + digest_data.get('to', []))

    es.index(
        index=settings.ELASTICSEARCH_INDEX,
        doc_type='doc',
        id=digest.id,
        body=data,
    )
