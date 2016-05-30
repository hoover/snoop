import simplejson as json
from django.core.management.base import BaseCommand
from maldini import models
from maldini import queue

class Command(BaseCommand):

    help = "Reset the `started` flag on jobs"

    def handle(self, verbosity, **options):
        def put_job(queue_name, id):
            data = {'id': id}
            if verbosity > 0: print(queue_name, data)
            queue.put(queue_name, data, verbose=verbosity > 0)

        if verbosity > 0: print('reading from pq digest queue ...')
        digest_queue = queue.get('digest')
        while True:
            task = digest_queue.get(block=False)
            if not task:
                break

            put_job('digest', task.data['id'])

        if verbosity > 0: print('reading from pq index queue ...')
        digest_queue = queue.get('index')
        while True:
            task = digest_queue.get(block=False)
            if not task:
                break

            put_job('index', task.data['id'])

        if verbosity > 0: print('reading from Error model ...')
        for err in models.Error.objects.all():
            put_job('digest', err.document_id)
            err.delete()
