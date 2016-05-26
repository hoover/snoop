import simplejson as json
from django.core.management.base import BaseCommand
from maldini import models

class Command(BaseCommand):

    help = "List errors from digest"

    def handle(self, **options):
        for error in models.Error.objects.all():
            print(error.created_at, error.document_id)
