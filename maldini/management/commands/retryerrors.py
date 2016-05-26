import simplejson as json
from django.core.management.base import BaseCommand
from maldini import models
from maldini import queue

class Command(BaseCommand):

    help = "Add errored documents back to queue"

    def handle(self, verbosity, **options):
        digest_queue = queue.get('digest')
        seen = set()
        for error in models.Error.objects.all():
            document_id = error.document_id

            if document_id not in seen:
                digest_queue.put({'id': document_id})
                seen.add(document_id)
                if verbosity > 0:
                    print(document_id)

            error.delete()
