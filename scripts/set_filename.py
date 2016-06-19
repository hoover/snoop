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

for doc in Document.objects.all().iterator():
    if doc.filename:
        continue
    if doc.container_id is None:
        doc.filename = Path(doc.path).name
    else:
        doc.filename = attachment_filenames(doc.container)[doc.path]
    doc.save()
