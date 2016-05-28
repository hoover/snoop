from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from maldini import models

class Command(BaseCommand):

    help = "Create fake folder entries"

    def handle(self, **options):
        root = Path(settings.MALDINI_ROOT)
        seen = set()
        file_docs = models.Document.objects.filter(container_id=None)
        n_created = n_existing = 0
        for document in file_docs.iterator():
            current = Path(document.path).parent
            while str(current) != '.':
                if current in seen:
                    break
                _, created = models.Document.objects.get_or_create(
                    path=current,
                    disk_size=0,
                    content_type='application/x-directory',
                )
                seen.add(current)
                if created:
                    n_created += 1
                else:
                    n_existing += 1

                current = current.parent

        print('folder entries:', n_created, 'created,', n_existing, 'existing')
