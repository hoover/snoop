import json
import random
import subprocess
import tempfile
from maldini import models, emails

EMAIL_CONTENT_TYPES = [
    'message/x-emlx',
    'message/rfc822',
    'application/vnd.ms-outlook',
]

id_list = list(
    models.Document
    .objects
    .filter(content_type__in=EMAIL_CONTENT_TYPES)
    .values_list('id', flat=True)
)
id_pool = set(id_list)

def diff(a, b, prefix):
    with tempfile.NamedTemporaryFile(prefix=prefix) as t1:
        with tempfile.NamedTemporaryFile(prefix=prefix) as t2:
            t1.write(json.dumps(a, indent=2, sort_keys=True).encode('utf-8'))
            t1.write(b'\n')
            t1.flush()
            t2.write(json.dumps(b, indent=2, sort_keys=True).encode('utf-8'))
            t2.write(b'\n')
            t2.flush()
            subprocess.call(
                'diff -u "{}" "{}" | less'.format(t1.name, t2.name),
                shell=True,
            )

def check(batch):
    sample_ids = set(random.sample(id_pool, min([batch, len(id_pool)])))
    for doc in models.Document.objects.filter(id__in=sample_ids).iterator():
        assert emails.is_email(doc)
        cache_row = models.EmailCache.objects.get(pk=doc.id)
        cached = json.loads(cache_row.value)
        correct = emails.raw_parse_email.no_cache(doc)
        if cached != correct:
            print('\n\n\n%d\n' % doc.id)
            diff(cached, correct, str(doc.id)+'-')
    id_pool.difference_update(sample_ids)

while id_pool:
  check(10)
