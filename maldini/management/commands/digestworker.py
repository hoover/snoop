import simplejson as json
from django.core.management.base import BaseCommand
from django.db import transaction
from maldini import models
from maldini import queue
from maldini.digest import digest

def perform_job(document):
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
            queue.get('digest').put({'id': child.id})
            if verbosity > 0:
                print('new child', child.id)

    models.Digest.objects.update_or_create(
        id=document.id,
        defaults={'data': json.dumps(data)},
    )

    queue.get('index').put({'id': document.id})

class Command(BaseCommand):

    help = "Run the `digest` worker"

    def handle(self, verbosity, **options):
        digest_queue = queue.get('digest')
        while True:
            task = digest_queue.get(block=False)
            if not task:
                break

            document_id = task.data['id']
            print(document_id)
            err = models.Error.objects.create(document_id=document_id)

            with transaction.atomic():
                try:
                    document = models.Document.objects.get(id=document_id)
                except models.Document.DoesNotExist:
                    print('MISSING')
                    continue

                try:
                    with transaction.atomic():
                        perform_job(document)

                except:
                    outcome = 'ERR'

                else:
                    outcome = 'OK'
                    err.delete()

                if verbosity > 0:
                    print(outcome)
