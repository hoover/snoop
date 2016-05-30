import simplejson as json
from django.core.management.base import BaseCommand
from django.db import transaction
from maldini import models
from maldini import queue
from maldini.digest import digest

class Command(BaseCommand):

    help = "Run the `digest` worker"

    def handle(self, verbosity, **options):
        digest_queue = queue.get('digest')
        index_queue = queue.get('index')
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
                        data = digest(document)
                        data_json = json.dumps(data)

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
                                digest_queue.put({'id': child.id})
                                if verbosity > 0:
                                    print('new child', child.id)

                except:
                    outcome = 'ERR'

                else:
                    outcome = 'OK'
                    models.Digest.objects.update_or_create(
                        id=document.id,
                        defaults={'data': data_json},
                    )
                    index_queue.put({'id': document.id})
                    err.delete()

                if verbosity > 0:
                    print(outcome)
