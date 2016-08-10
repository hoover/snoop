import simplejson as json
from django.core.management.base import BaseCommand
from ... import models

class Command(BaseCommand):

    help = "Reset the `started` flag on jobs"

    def add_arguments(self, parser):
        parser.add_argument('queue')

    def handle(self, queue, verbosity, **options):
        rows = (
            models.Job
            .objects
            .filter(queue=queue, started=True)
            .update(started=False)
        )
        print("updated", rows, "rows")
