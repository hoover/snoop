from django.core.management.base import BaseCommand
from django.conf import settings
from ...walker import Walker

class Command(BaseCommand):

    help = "Traverse directory and get fiels"

    def add_arguments(self, parser):
        parser.add_argument('prefix', nargs='?', default=None)
        parser.add_argument('-r', action='store_true', dest='restart')

    def handle(self, prefix, restart, **options):
        Walker.walk(0, settings.MALDINI_ROOT, prefix, restart)
