import simplejson as json
from django.core.management.base import BaseCommand
from maldini import models
from maldini.prepare import extract

class Command(BaseCommand):

    help = "Run the `process` worker"

    def handle(self, **options):
        for document in models.Document.objects.iterator():
            data = extract(document)
            models.Cache.objects.update_or_create(
                document=document,
                defaults={'data': json.dumps(data)},
            )
