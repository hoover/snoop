from django.core.management.base import BaseCommand
from django.conf import settings
from maldini.walker import Walker

class Command(BaseCommand):

    help = "Traverse directory and get fiels"

    def add_arguments(self, parser):
        parser.add_argument('prefix', nargs='?', default=None)

    def handle(self, prefix, **options):
        Walker.walk(0, settings.MALDINI_ROOT, prefix)
