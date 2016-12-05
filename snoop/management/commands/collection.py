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
            dest='es_index',
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
        parser.add_argument(
            '--set-ocr',
            nargs=2,
            dest='ocr',
            default=None,
            help='[--set-ocr TAG PATH] Add or modify the path for an OCR file set'
        )
        parser.add_argument(
            '--remove-ocr',
            dest='remove_ocr',
            default=None,
            help='Remove a path for an OCR file set'
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
        modify_ocr_data(collection, **options)
        print_info_for_collections([collection])


def print_all_collections():
    print_info_for_collections(models.Collection.objects.all().order_by('id'))


def print_info_for_collections(collections):
    template = "{:4s} {:15s} {:20s} {:20s} {:35s} {:s}"
    head_line = template.format("ID", "SLUG", "ES INDEX", "TITLE", "DESCRIPTION", "OCR")
    print(head_line)
    for c in collections:
        c_line = template.format(str(c.id), c.slug, c.es_index, c.title, c.description, str(c.ocr))
        print(c_line)

def modify_ocr_data(collection, **options):
    modified = False
    if options['ocr'] is not None:
        tag, path = options['ocr']
        collection.ocr[tag] = path
        modified = True
    if options['remove_ocr'] is not None:
        del collection.ocr[options['remove_ocr']]
        modified = True
    if modified:
        collection.save()

def modify_collection(collection, **options):
    keys = {
        'path',
        'slug',
        'es_index',
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

