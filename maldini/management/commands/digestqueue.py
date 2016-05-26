import simplejson as json
from django.core.management.base import BaseCommand
from maldini import models
from maldini import queue

class Command(BaseCommand):

    help = "Add documents to the digest queue"

    def add_arguments(self, parser):
        parser.add_argument('where')

    def handle(self, where, verbosity, **options):
        digest_queue = queue.get('digest')
        query = 'SELECT id FROM maldini_document WHERE %s' % where
        for document in models.Document.objects.raw(query):
            digest_queue.put({'id': document.id})
            if verbosity > 1:
                print(document.id)
