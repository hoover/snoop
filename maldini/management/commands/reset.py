from django.core.management.base import BaseCommand
from django.conf import settings
from maldini import models

class Command(BaseCommand):

    help = "Reset the database, removing all documents"

    def handle(self, **options):
        models.Job.objects.all().delete()
        models.Digest.objects.all().delete()
        models.FolderMark.objects.all().delete()
        models.Document.objects.all().delete()
