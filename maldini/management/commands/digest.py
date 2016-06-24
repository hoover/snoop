import simplejson as json
from django.core.management.base import BaseCommand
from maldini import models
from maldini import digest

class Command(BaseCommand):

    help = "Digest one document"

    def add_arguments(self, parser):
        parser.add_argument('document_id', type=int)
        parser.add_argument('-c', action='store_true', dest='children')

    def handle(self, document_id, children, **options):
        document = models.Document.objects.get(id=document_id)
        data = digest.digest(document)
        print(json.dumps(data, indent=2))
        if children:
            digest.create_children(document, data, verbose=True)
