import simplejson as json
from django.core.management.base import BaseCommand
from maldini import models
from maldini import queue

class Command(BaseCommand):

    help = "Add documents to the index queue"

    def add_arguments(self, parser):
        parser.add_argument('where')

    def handle(self, where, verbosity, **options):
        query = 'SELECT id FROM maldini_document WHERE %s' % where
        for document in models.Document.objects.raw(query):
            queue.put('index', {'id': document.id}, verbose=verbosity>0)
            if verbosity > 0:
                print(document.id)
