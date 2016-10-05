import simplejson as json
from django.core.management.base import BaseCommand
from ... import models
from ... import queues
from ... import utils

class Command(BaseCommand):

    help = "Add documents to the digest queue"

    def add_arguments(self, parser):
        parser.add_argument('--where', default='true',
            help='SQL "WHERE" clause on the snoop_document table')

    def handle(self, where, verbosity, **options):
        query = utils.build_raw_query('snoop_document', where)
        for document in models.Document.objects.raw(query):
            queues.put('digest', {'id': document.id}, verbose=verbosity>0)
            if verbosity > 0:
                print(document.id)
