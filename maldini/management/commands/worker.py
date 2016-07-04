from django.core.management.base import BaseCommand
from maldini import queues

class Command(BaseCommand):

    help = "Run a worker"

    def add_arguments(self, parser):
        parser.add_argument('queue')
        parser.add_argument('-x', action='store_true', dest='stop_first_error')

    def handle(self, verbosity, queue, stop_first_error, **options):
        if queue == 'digest':
            from maldini.digest import worker
        elif queue == 'index':
            from maldini.index import worker
        elif queue == 'ocr':
            from maldini.ocr import worker
        elif queue == 'hotfix':
            from maldini.hotfix import worker
        else:
            raise ValueError("Unknown queue %r" % queue)

        queue_iterator = queues.iterate(
            queue,
            verbose=verbosity > 0,
            stop_first_error=stop_first_error,
            in_order=stop_first_error,
        )

        for work in queue_iterator:
            with work() as data:
                worker(**data, verbose=verbosity>0)
