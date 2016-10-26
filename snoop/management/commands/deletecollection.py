from django.core.management.base import BaseCommand
from ... import models

class Command(BaseCommand):

    help = "Delete a document collection"

    def add_arguments(self, parser):
        parser.add_argument(
            'slug',
            help="The slug of the collection to delete. Should not contain spaces.",
        )

    def handle(self, slug, **options):
        try:
            c = models.Collection.objects.get(slug=slug)
        except models.Collection.DoesNotExist:
            print("Collection with slug", slug, "does not exist.")
            return

        num_documents = c.document_set.count()
        if num_documents > 0:
            print("The collection with slug", slug, "still has", str(num_documents), "available.")
            print("Please delete those documents first, or move them to another collection.")
            return

        c.delete()

        print("Collection with slug", c.slug, "was deleted.")
