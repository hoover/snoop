from contextlib import contextmanager
from django.db import connection, transaction, IntegrityError
import pq
from . import models

@contextmanager
def django_transaction(conn, **kwargs):
    assert conn is connection
    with transaction.atomic():
        yield conn.cursor(**kwargs)

pq.transaction = django_transaction

def _create():
    pq.PQ(connection).create()

def _cleanup():
    cursor = connection.cursor()
    cursor.execute('drop table queue')
    cursor.execute('drop function pq_notify()')

def get(name):
    return pq.PQ(connection)[name]

def put(queue, data, verbose=False):
    try:
        models.Job.objects.create(queue=queue, data=data)
    except IntegrityError:
        if verbose: print('job already exists, skipping:', queue, data)

def iterate(queue, verbose=False, stop_first_error=False):
    while True:
        with transaction.atomic():
            job = (
                models.Job.objects
                .select_for_update()
                .filter(queue=queue)
                .filter(started=False)
                .first()
            )

            if job is None:
                if verbose: print('No jobs available in', queue)
                return

            job.started = True
            job.save()

        if verbose: print(job.data)

        @contextmanager
        def work():
            try:
                yield job.data

            except Exception:
                if stop_first_error:
                    job.started = False
                    job.save()
                    raise

                elif verbose:
                    print('ERR')

            else:
                # no error; delete the job
                if verbose: print('OK')
                job.delete()

        yield work
