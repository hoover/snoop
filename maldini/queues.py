from contextlib import contextmanager
from django.db import transaction, IntegrityError
from . import models

def put(queue, data, verbose=False):
    try:
        models.Job.objects.create(queue=queue, data=data)
    except IntegrityError:
        if verbose: print('job already exists, skipping:', queue, data)

def iterate(queue, verbose=False, stop_first_error=False, in_order=False):
    while True:
        with transaction.atomic():
            try:
                query = (
                    models.Job.objects
                    .select_for_update()
                    .filter(queue=queue)
                    .filter(started=False)
                )
                if in_order:
                    query = query.order_by('id')
                job = query[0]

            except IndexError:
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

def bulk(queue, batch, verbose=False):
    while True:
        with transaction.atomic():
            query = (
                models.Job.objects
                .select_for_update()
                .filter(queue=queue)
                .filter(started=False)
            )
            jobs = list(query[:batch])

            if not jobs:
                if verbose: print('No jobs available in', queue)
                return

            job_ids = [job.id for job in jobs]
            job_collection = models.Job.objects.filter(id__in=job_ids)

            job_collection.update(started=True)

        if verbose: print(len(job_ids), 'jobs')

        @contextmanager
        def work():
            try:
                yield [job.data for job in jobs]

            except Exception:
                print('ERR')

            else:
                # no error; delete the job
                if verbose: print('OK')
                job_collection.delete()

        yield work
