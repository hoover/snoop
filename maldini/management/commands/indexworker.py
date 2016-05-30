from django.core.management.base import BaseCommand
from maldini import queues
from maldini import workers

class Command(BaseCommand):

    help = "Run the `index` worker"

    def add_arguments(self, parser):
        parser.add_argument('-x', action='store_true', dest='stop_first_error')

    def handle(self, verbosity, stop_first_error, **options):
        queue_iterator = queues.iterate(
            'index',
            verbose=verbosity > 0,
            stop_first_error=stop_first_error,
        )

        for work in queue_iterator:
            with work() as data:
                workers.index(**data, verbose=verbosity>0)
