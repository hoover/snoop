from django.core.management.base import BaseCommand
import os, sys
from ... import models

class Command(BaseCommand):

    help = "Create a new document collection"

    def add_arguments(self, parser):
        parser.add_argument(
            "path",
            help="The full, absolute path where the documents are located."
        )
        parser.add_argument(
            'slug',
            help="The slug of the collection to create. Should not contain spaces.",
        )
        parser.add_argument(
            "es_index",
            help='The Elasticsearch index for the collection.',
        )
        parser.add_argument(
            "title",
            help='The user-readable title of the collection.',
        )
        parser.add_argument(
            "description",
            default="",
            help="The user-readable description for the new collection.",
        )

    def handle(self, path, slug, es_index, title, description, **options):
        if not os.path.exists(path):
            print("The path", path, "does not exist.")
            print("Please check the provided path.")
            sys.exit(1)

        if not os.path.isabs(path):
            print("The path", path, "is not absolute.")
            print("Please provide an absolute path.")
            sys.exit(1)

        c = models.Collection(
            path=path,
            slug=slug,
            es_index=es_index,
            title=title,
            description=description,
        )
        c.save()
        print("Collection saved with id", c.id)

