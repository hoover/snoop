from django.core.management.base import BaseCommand
from django.conf import settings
from maldini.prepare import Walker

class Command(BaseCommand):

    help = "Push files to ES"

    def handle(self, **options):
        from elasticsearch import Elasticsearch, helpers
        from elasticsearch.client.utils import _make_path
        from elasticsearch.exceptions import NotFoundError, TransportError

        from maldini.models import Document

        es = Elasticsearch(settings.ELASTICSEARCH_URL)

        for doc in Document.objects.all():
            data = {
                'path': doc.path,
                'disk_size': doc.disk_size,
            }
            es.index(
                index='hoover-6',
                doc_type='doc',
                id=doc.path,
                body=data,
            )
            print(doc.path)
