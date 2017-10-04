from django.core.management.base import BaseCommand
from django.conf import settings
from elasticsearch import Elasticsearch

es = Elasticsearch(
    settings.SNOOP_ELASTICSEARCH_URL,
    timeout=settings.SNOOP_ELASTICSEARCH_TIMEOUT,
)

class Command(BaseCommand):

    help = "ES status"

    def handle(self, **options):
        print('count:', es.count()['count'])
