from contextlib import contextmanager
from django.db import connection, transaction
import pq

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
