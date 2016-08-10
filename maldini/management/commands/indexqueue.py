import simplejson as json
from django.core.management.base import BaseCommand
from ... import models
from ... import queues

class Command(BaseCommand):

    help = "Add documents to the index queue"

    def add_arguments(self, parser):
        parser.add_argument('where')

    def handle(self, where, verbosity, **options):
        query = 'SELECT id FROM maldini_document WHERE %s' % where
        for document in models.Document.objects.raw(query):
            queues.put('index', {'id': document.id}, verbose=verbosity>0)
            if verbosity > 0:
                print(document.id)
