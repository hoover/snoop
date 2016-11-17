import sys
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
            sys.exit(1)

        num_documents = c.document_set.count()
        if num_documents > 0:
            print("The collection with slug", slug, "still has", str(num_documents), "available.")
            print("Are you sure you want to delete the", slug, "collection with all its documents?")
            print("This operation cannot be undone.")
            confirm = input("Type YES to delete the {} collection".format(c.slug))
            if confirm != 'YES':
                print("You typed something other than 'YES', aborting.")
                return
            c.document_set.delete()
            print("The", str(num_documents), "for collection", slug, "have been deleted.")

        c.delete()

        print("Collection with slug", c.slug, "was deleted.")
