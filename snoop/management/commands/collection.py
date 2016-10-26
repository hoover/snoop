import sys
from django.core.management.base import BaseCommand
from ... import models

class Command(BaseCommand):

    help = "View and modify a document collection"

    def add_arguments(self, parser):
        parser.add_argument(
            'collection_slug',
            nargs='?',
            default=None,
            help="The slug of the collection to view/modify"
        )
        parser.add_argument(
            '--set-path',
            dest='path',
            default=None,
            help='Modify the path for the collection'
        )
        parser.add_argument(
            '--set-title',
            dest='title',
            default=None,
            help='Modify the user-readable title for the collection'
        )
        parser.add_argument(
            '--set-es-index',
            dest='index',
            default=None,
            help='Modify the Elasticsearch index for the collection'
        )
        parser.add_argument(
            '--set-slug',
            dest='slug',
            default=None,
            help='Modify the slug for the collection'
        )
        parser.add_argument(
            '--set-description',
            dest='description',
            default=None,
            help='Modify the single-line user-readable for the collection'
        )

    def handle(self, collection_slug, **options):
        if not collection_slug:
            print_all_collections()
            return

        try:
            collection = models.Collection.objects.filter(slug=collection_slug).get()
        except models.Collection.DoesNotExist:
            print("Collection with slug", collection_slug, "does not exist.")
            sys.exit(1)

        modify_collection(collection, **options)
        print_info_for_collections([collection])


def print_all_collections():
    print_info_for_collections(models.Collection.objects.all().order_by('id'))


def print_info_for_collections(collections):
    template = "{:4s} {:15s} {:20s} {:30s} {:s}"
    head_line = template.format("ID", "SLUG", "ES INDEX", "TITLE", "DESCRIPTION")
    print(head_line)
    for c in collections:
        c_line = template.format(str(c.id), c.slug, c.es_index, c.title, c.description)
        print(c_line)


def modify_collection(collection, **options):
    keys = {
        'path',
        'slug',
        'index',
        'title',
        'description'
    }
    modified = False
    for key in keys:
        if options[key] is not None:
            setattr(collection, key, options[key])
            modified = True
    if modified:
        collection.save()

