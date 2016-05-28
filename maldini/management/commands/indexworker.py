import simplejson as json
from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings
from elasticsearch import Elasticsearch
from maldini import models
from maldini import queue

es = Elasticsearch(settings.ELASTICSEARCH_URL)

class Command(BaseCommand):

    help = "Run the `index` worker"

    def handle(self, verbosity, **options):
        index_queue = queue.get('index')
        while True:
            with transaction.atomic():
                task = index_queue.get(block=False)
                if not task:
                    break

                digest = models.Digest.objects.get(id=task.data['id'])
                alldata = json.loads(digest.data)

                data = {
                    'text': alldata.get('text'),
                }

                if verbosity > 1:
                    print(data)

                es.index(
                    index=settings.ELASTICSEARCH_INDEX,
                    doc_type='doc',
                    id=digest.id,
                    body=data,
                )

                if verbosity > 0:
                    print(digest.id)
