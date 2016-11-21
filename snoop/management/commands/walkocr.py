import sys
from django.core.management.base import BaseCommand
from ... import models
from ...ocr import walk

class Command(BaseCommand):

    help = "Ingest OCRed files"

    def add_arguments(self, parser):
        parser.add_argument(
            'collection_slug',
            default=None,
            help="The slug of the collection"
        )
        parser.add_argument(
            'tag',
            default=None,
            help="The key of the OCR file set"
        )

    def handle(self, verbosity, collection_slug, tag, **options):
        try:
            c = models.Collection.objects.get(slug=collection_slug)
        except models.Collection.DoesNotExist:
            print("Collection with slug", collection_slug, "does not exist.")
            sys.exit(1)
        if tag not in c.ocr:
            print("Collection with slug", collection_slug, "does not have OCR key", tag)
            sys.exit(1)
        ocr_path = c.ocr[tag]
        walk(c, tag, ocr_path, verbose=verbosity > 0)
