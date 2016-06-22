from pathlib import Path
from functools import lru_cache
from maldini.models import Document
from maldini.digest import digest

@lru_cache(1000000)
def attachment_filenames(doc):
    data = digest(doc)
    return {
        name: info['filename']
        for name, info in data['attachments'].items()
    }

def progress_meter(every=1000, msg="{n} items"):
    import itertools
    for n in itertools.count(1):
        if n % every == 0:
            print(msg.format(n=n))
        yield

def set_filenames():
    meter = progress_meter(every=100)
    for doc in Document.objects.filter(filename='').iterator():
        if doc.filename:
            continue
        if doc.container_id is None:
            doc.filename = Path(doc.path).name
        else:
            doc.filename = attachment_filenames(doc.container)[doc.path]
        doc.save()
        next(meter)

set_filenames()
