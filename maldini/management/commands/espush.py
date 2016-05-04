from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from elasticsearch import Elasticsearch
from maldini.models import Document
from maldini.prepare import EmailParser

es = Elasticsearch(settings.ELASTICSEARCH_URL)

def extract(doc):
    file = Path(settings.MALDINI_ROOT) / doc.path
    data = {
        'title': doc.path,
        'path': doc.path,
        'disk_size': doc.disk_size,
    }

    if file.suffix == '.emlx':
        (text, warnings, flags, size_disk) = EmailParser.parse(file)
        data['text'] = text

    return data

def push(doc):
    print(doc.id, doc.path)

    try:
        data = extract(doc)

    except:
        #doc.fail = True
        #doc.save()
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
