import json
import random
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

def check(batch):
    sample_ids = set(random.sample(id_list, batch))
    errors = []
    for doc in models.Document.objects.filter(id__in=sample_ids).iterator():
        assert emails.is_email(doc)
        cache_row = models.EmailCache.objects.get(pk=doc.id)
        cached = json.loads(cache_row.value)
        correct = emails.raw_parse_email.no_cache(doc)
        if cached != correct:
            errors.append(doc.id)
    id_pool.difference_update(sample_ids)
    return errors

batch = 1000
n = 0
while id_pool:
  n += 1
  print(n * batch, check(batch))
