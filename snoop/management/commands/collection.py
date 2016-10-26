from django.core.management.base import BaseCommand
from ... import models

class Command(BaseCommand):

    help = "View and modify a document collection"

    def add_arguments(self, parser):
        parser.add_argument(
            'slug',
            nargs='?',
            default=None,
            help="The slug of the collection to view/modify"
        )
        parser.add_argument(
            '--set-path',
            dest='set_path',
            default=None,
            help='Modify the path for the collection'
        )
        parser.add_argument(
            '--set-title',
            dest='set_title',
            default=None,
            help='Modify the user-readable title for the collection'
        )
        parser.add_argument(
            '--set-es-index',
            dest='set_index',
            default=None,
            help='Modify the Elasticsearch index for the collection'
        )
        parser.add_argument(
            '--set-slug',
            dest='set_slug',
            default=None,
            help='Modify the slug for the collection'
        )
        parser.add_argument(
            '--set-description',
            dest='set_description',
            default=None,
            help='Modify the single-line user-readable for the collection'
        )

    def handle(self, slug, all, **options):
        if not slug:
            print_all_collections()
            return

        try:
            collection = models.Collection.objects.filter(slug=slug).get()
        except models.Collection.DoesNotExist:
            print("Collection with slug", slug, "does not exist.")
            return

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
    options = {k: options[k] for k in options.keys() if options[k] if not None}
    keys = {
        'set_path',
        'set_slug',
        'set_index',
        'set_title',
        'set_description'
    }
    modified = set(options.keys()).intersection(keys)
    if not modified:
        return

    if 'set_path' in options:
        collection.path = options['set_path']
    if 'set_slug' in options:
        collection.slug = options['set_slug']
    if 'set_index' in options:
        collection.es_index = options['set_index']
    if 'set_title' in options:
        collection.title = options['set_title']
    if 'set_description' in options:
        collection.description = options['set_description']
    collection.save()

