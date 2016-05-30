import simplejson as json
from django.core.management.base import BaseCommand
from maldini import models

class Command(BaseCommand):

    help = "Reset the `started` flag on jobs"

    def add_arguments(self, parser):
        parser.add_argument('queue')

    def handle(self, queue, verbosity, **options):
        for job in models.Job.objects.filter(queue=queue, started=True):
            if verbosity > 0:
                print(job.data)
            job.started = False
            job.save()
