from django.core.management.base import BaseCommand
from maldini import queues

class Command(BaseCommand):

    help = "Run a worker in bulk"

    def add_arguments(self, parser):
        parser.add_argument('queue')
        parser.add_argument('-b', type=int, dest='batch', default=100)

    def handle(self, verbosity, queue, batch, **options):
        if queue == 'index':
            from maldini.index import bulk_worker
        else:
            raise ValueError("Unknown queue %r" % queue)

        queue_iterator = queues.bulk(
            queue,
            batch=batch,
            verbose=verbosity > 0,
        )

        for work in queue_iterator:
            with work() as data_list:
                bulk_worker(data_list, verbose=verbosity>0)
