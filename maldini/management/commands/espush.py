import simplejson as json
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from elasticsearch import Elasticsearch
from maldini.models import Document, Generation, Failure, Cache
from maldini.digest import digest

es = Elasticsearch(settings.ELASTICSEARCH_URL)

class Command(BaseCommand):

    help = "Push files to ES"

    def handle(self, **options):

        offset = 0
        for doc in Document.objects.exclude(generation__n=1).order_by('id').all().iterator():
            print(doc.id, doc.path)

            try:
                data = digest(doc)
                data_json = json.dumps(data)

            except KeyboardInterrupt:
                raise

            except:
                Failure.objects.create(document=doc)
                print 'ERROR'

            else:
                Cache.objects.create(document=doc, data=data_json)

            Generation.objects.create(document=doc, n=1)

            #es.index(
            #    index='hoover-6',
            #    doc_type='doc',
            #    id=doc.id,
            #    body=data,
            #)
            #doc.push = False
            #doc.save()
