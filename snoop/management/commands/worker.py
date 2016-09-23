from django.core.management.base import BaseCommand
from ... import queues
from ...utils import log_result

@log_result()
def run_worker(worker, queue_name, queue_iterator, verbose):
    num_items = 0
    for work in queue_iterator:
        with work() as data:
            num_items += 1
            worker(verbose=verbose, **data)

    return {
        'type': 'job',
        'queue': queue_name,
        'items': num_items,
    }

class Command(BaseCommand):

    help = "Run a worker"

    def add_arguments(self, parser):
        parser.add_argument('queue')
        parser.add_argument('-x', action='store_true', dest='stop_first_error')

    def handle(self, verbosity, queue, stop_first_error, **options):
        if queue == 'digest':
            from ...digest import worker
        elif queue == 'index':
            from ...index import worker
        elif queue == 'ocr':
            from ...ocr import worker
        elif queue == 'hotfix':
            from ...hotfix import worker
        else:
            raise ValueError("Unknown queue %r" % queue)

        queue_iterator = queues.iterate(
            queue,
            verbose=verbosity > 0,
            stop_first_error=stop_first_error,
            in_order=stop_first_error,
        )

        run_worker(worker, queue, queue_iterator, verbosity>0)
