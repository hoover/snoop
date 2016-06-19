from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from maldini import models

FOLDER = 'application/x-directory'
BATCH_SIZE = 100

class Command(BaseCommand):

    help = "Create fake folder entries"

    def handle(self, **options):
        root = Path(settings.MALDINI_ROOT)
        seen = set(d.path for d in models.Document.objects.filter(
            container_id=None, content_type=FOLDER))
        file_docs = models.Document.objects.filter(container_id=None)
        n_created = 0

        def create_batch():
            models.Document.objects.bulk_create([
                models.Document(
                    path=p,
                    disk_size=0,
                    content_type=FOLDER,
                    filename=p.name,
                )
                for p in batch
            ])
            n = len(batch)
            batch[:] = []
            return n

        batch = []
        for document in file_docs.iterator():
            current = Path(document.path).parent
            while str(current) != '.':
                if current in seen:
                    break
                batch.append(current)
                seen.add(current)
                current = current.parent

                if len(batch) >= BATCH_SIZE:
                    n_created += create_batch()

        if batch:
            n_created += create_batch()

        print('folder entries:', n_created, 'created,', len(seen), 'total')
