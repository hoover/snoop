from django.core.management.base import BaseCommand

class Command(BaseCommand):

    help = "Traverse directory and get fiels"

    def add_arguments(self, parser):
        parser.add_argument('prefix')

    def handle(self, prefix, **options):
        print repr(prefix.decode('utf-8'))
