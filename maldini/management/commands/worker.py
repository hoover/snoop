from django.core.management.base import BaseCommand
from maldini import queues
from maldini import workers

class Command(BaseCommand):

    help = "Run the `digest` worker"

    def add_arguments(self, parser):
        parser.add_argument('queue')
        parser.add_argument('-x', action='store_true', dest='stop_first_error')

    def handle(self, verbosity, queue, stop_first_error, **options):
        if queue == 'digest':
            worker = workers.digest
        elif queue == 'index':
            worker = workers.index
        else:
            raise ValueError("Unknown queue %r" % queue)

        queue_iterator = queues.iterate(
            queue,
            verbose=verbosity > 0,
            stop_first_error=stop_first_error,
        )

        for work in queue_iterator:
            with work() as data:
                worker(**data, verbose=verbosity>0)