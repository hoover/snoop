import simplejson as json
from django.core.management.base import BaseCommand
from maldini import models
from maldini.digest import digest

class Command(BaseCommand):

    help = "Run the `digest` worker"

    def handle(self, **options):
        for document in models.Document.objects.iterator():
            data = digest(document)
            models.Digest.objects.update_or_create(
                id=document.id,
                defaults={'data': json.dumps(data)},
            )
