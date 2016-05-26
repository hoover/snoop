import simplejson as json
from django.core.management.base import BaseCommand
from maldini import models
from maldini.digest import digest

class Command(BaseCommand):

    help = "Digest one document"

    def add_arguments(self, parser):
        parser.add_argument('document_id', type=int)

    def handle(self, document_id, **options):
        document = models.Document.objects.get(id=document_id)
        print(json.dumps(digest(document), indent=2))
