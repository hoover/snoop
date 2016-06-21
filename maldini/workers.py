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

    alldata = json.loads(digest.data)

    data = {
        'title': alldata.get('title'),
        'path': alldata.get('path'),
        'text': alldata.get('text'),
        'subject': alldata.get('subject'),
        'date': alldata.get('date'),
        'people': ' '.join([alldata.get('from', '')] + alldata.get('to', [])),
        'filetype': alldata.get('type'),
        'sha1': alldata.get('sha1'),
        'md5': alldata.get('md5'),
        'lang': alldata.get('lang'),
        'date_created': alldata.get('date_created'),
    }

    es.index(
        index=settings.ELASTICSEARCH_INDEX,
        doc_type='doc',
        id=digest.id,
        body=data,
    )
