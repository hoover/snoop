from django.core.management.base import BaseCommand
from django.conf import settings
from ... import models

class Command(BaseCommand):

    help = "Reset the database, removing all documents"

    def add_arguments(self, parser):
        parser.add_argument('-y', action='store_true', dest='really')

    def handle(self, really, **options):
        if really:
            models.Job.objects.all().delete()
            models.Digest.objects.all().delete()
            models.FolderMark.objects.all().delete()
            models.Document.objects.all().delete()

        else:
            print("Not deleting anything; pass -y as flag")
