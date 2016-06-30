from django.core.management.base import BaseCommand
from django.conf import settings
from maldini.ocr import walk

class Command(BaseCommand):

    help = "Ingest OCRed files"

    def add_arguments(self, parser):
        parser.add_argument('tag')
        parser.add_argument('subfolder')

    def handle(self, verbosity, tag, subfolder, **options):
        walk(tag, subfolder, verbose=verbosity > 0)
