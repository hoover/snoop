from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from elasticsearch import Elasticsearch
from maldini.models import Document
from maldini.prepare import extract

es = Elasticsearch(settings.ELASTICSEARCH_URL)

def push(doc):
    print(doc.id, doc.path)

    try:
        data = extract(doc)

    except KeyboardInterrupt:
        raise

    except:
        #doc.fail = True
        doc.status = {'error': True}
        doc.save()
        print 'ERROR'
        return

    es.index(
        index='hoover-6',
        doc_type='doc',
        id=doc.id,
        body=data,
    )
    #doc.push = False
    #doc.save()


class Command(BaseCommand):

    help = "Push files to ES"

    def handle(self, **options):

        offset = 0
        while True:
            chunk = list(Document.objects.order_by('id').all()[offset:offset+100])

            if not chunk:
                break

            for doc in chunk:
                push(doc)

            offset += 100
