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
        while True:
            with transaction.atomic():
                task = digest_queue.get(block=False)
                if not task:
                    break

                document = models.Document.objects.get(id=task.data['id'])

                try:
                    with transaction.atomic():
                        data = json.dumps(digest(document))

                except:
                    outcome = 'ERR'
                    models.Error.objects.create(document_id=document.id)

                else:
                    outcome = 'OK'
                    models.Digest.objects.update_or_create(
                        id=document.id,
                        defaults={'data': data},
                    )

                if verbosity > 0:
                    print(document.id, outcome)
