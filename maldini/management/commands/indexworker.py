import simplejson as json
from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings
from elasticsearch import Elasticsearch
from maldini import models
from maldini import queue

es = Elasticsearch(settings.ELASTICSEARCH_URL)

def perform_job(id, verbose):
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
    }

    es.index(
        index=settings.ELASTICSEARCH_INDEX,
        doc_type='doc',
        id=digest.id,
        body=data,
    )

class Command(BaseCommand):

    help = "Run the `index` worker"

    def add_arguments(self, parser):
        parser.add_argument('-x', action='store_true', dest='stop_first_error')

    def handle(self, verbosity, stop_first_error, **options):
        queue_iterator = queue.iterate(
            'index',
            verbose=verbosity > 0,
            stop_first_error=stop_first_error,
        )

        for work in queue_iterator:
            with work() as data:
                perform_job(**data, verbose=verbosity>0)
