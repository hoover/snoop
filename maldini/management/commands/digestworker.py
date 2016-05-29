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
            with transaction.atomic():
                task = digest_queue.get(block=False)
                if not task:
                    break

                document = models.Document.objects.get(id=task.data['id'])

                try:
                    with transaction.atomic():
                        data = digest(document)
                        data_json = json.dumps(data)

                except:
                    outcome = 'ERR'
                    models.Error.objects.create(document_id=document.id)

                else:
                    outcome = 'OK'
                    models.Digest.objects.update_or_create(
                        id=document.id,
                        defaults={'data': data_json},
                    )
                    index_queue.put({'id': document.id})

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

                if verbosity > 0:
                    print(document.id, outcome)
