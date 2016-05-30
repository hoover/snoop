import simplejson as json
from django.core.management.base import BaseCommand
from django.db import transaction
from maldini import models
from maldini import queue
from maldini.digest import digest

def perform_job(id, verbose):
    try:
        document = models.Document.objects.get(id=id)
    except models.Document.DoesNotExist:
        if verbose: print('MISSING')
        return

    data = digest(document)

    for name, info in data.get('attachments', {}).items():
        child, created = models.Document.objects.update_or_create(
            container=document,
            path=name,
            defaults={
                'disk_size': 0,
                'content_type': info['content_type'],
            },
        )

        if created:
            queue.put('digest', {'id': child.id}, verbose=verbose)
            if verbosity > 0:
                if verbose: print('new child', child.id)

    models.Digest.objects.update_or_create(
        id=document.id,
        defaults={'data': json.dumps(data)},
    )

    queue.put('index', {'id': document.id}, verbose=verbose)

class Command(BaseCommand):

    help = "Run the `digest` worker"

    def add_arguments(self, parser):
        parser.add_argument('-x', action='store_true', dest='stop_first_error')

    def handle(self, verbosity, stop_first_error, **options):
        queue_iterator = queue.iterate(
            'digest',
            verbose=verbosity > 0,
            stop_first_error=stop_first_error,
        )

        for work in queue_iterator:
            with work() as data:
                perform_job(**data, verbose=verbosity>0)
