from django.core.management.base import BaseCommand
from django.conf import settings
from ...walker import Walker
from ... import models

class Command(BaseCommand):

    help = "Traverse directory and get fiels"

    def add_arguments(self, parser):
        parser.add_argument('collection_slug')
        parser.add_argument('prefix', nargs='?', default=None)

    def handle(self, collection_slug, prefix, **options):
        try:
            collection = models.Collection.objects.get(slug=collection_slug)
        except models.Collection.DoesNotExist:
            print("Collection with slug", collection_slug, "does not exist.")
            return

        Walker.walk(
            root=collection.path,
            prefix=prefix,
            container_doc=None,
            collection_id=collection.id
        )
