from datetime import datetime, timezone
from time import time
from pathlib import Path
import json
from django.core.management.base import BaseCommand
from django.conf import settings
from ... import queues
from ...utils import append_with_lock

def log_function(fn, kwargs, data=None):
    """
    Logs to settings.SNOOP_LOG_DIR the result of running fn.
    :arg fn: a function that should return a dict with any values that should
             be logged
    :arg args: a dict with the keyword arguments that are passed to fn
    :arg data: a dict with more data that will be added to the log
    """

    if settings.SNOOP_LOG_DIR is None:
        fn(**kwargs)
        return

    time_stared = datetime.now(timezone.utc).astimezone().isoformat()

    t0 = time()
    fn_result = fn(**kwargs)
    duration = time() - t0

    if not data:
        data = fn_result
    else:
        data.update(fn_result)
    data['ok'] = 'error' not in data
    data['started'] = time_stared
    data['duration'] = duration

    log_line = json.dumps(data) + '\n'
    print(log_line)
    day = datetime.utcfromtimestamp(t0).date().isoformat()
    logfile = Path(settings.SNOOP_LOG_DIR) / (day + '.txt')
    logfile_path = str(logfile.absolute())
    append_with_lock(logfile_path, log_line)

def run_worker(worker, queue_name, queue_iterator, verbose):
    num_items = 0
    for work in queue_iterator:
        with work() as worker_arguments:
            num_items += 1
            worker_arguments['verbose'] = verbose
            item_data = {
                'type': 'worker',
                'queue': queue_name,
            }
            log_function(fn=worker, kwargs=worker_arguments, data=item_data)

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

        log_function(run_worker, {
            "worker": worker,
            "queue_name": queue,
            "queue_iterator": queue_iterator,
            "verbose": verbosity > 0
        })
