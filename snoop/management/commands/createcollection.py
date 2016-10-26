from django.core.management.base import BaseCommand
from ... import models

class Command(BaseCommand):

    help = "Create a new document collection"

    def add_arguments(self, parser):
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

    def handle(self, slug, es_index, title, description, **options):
        c = models.Collection(
            slug=slug,
            es_index=es_index,
            title=title,
            description=description,
        )
        c.save()
        print("Collection saved with id", c.id)

