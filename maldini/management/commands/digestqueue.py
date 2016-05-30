import simplejson as json
from django.core.management.base import BaseCommand
from maldini import models
from maldini import queues

class Command(BaseCommand):

    help = "Add documents to the digest queue"

    def add_arguments(self, parser):
        parser.add_argument('where')

    def handle(self, where, verbosity, **options):
        query = 'SELECT id FROM maldini_document WHERE %s' % where
        for document in models.Document.objects.raw(query):
            queues.put('digest', {'id': document.id}, verbose=verbosity>0)
            if verbosity > 0:
                print(document.id)
