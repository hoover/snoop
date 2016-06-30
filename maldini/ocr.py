from pathlib import Path
from collections import defaultdict
import re
from django.conf import settings
from . import models
from .utils import pdftotext
from . import queues

def walk(tag, verbose=False):

    def _traverse(folder, prefix=''):
        for item in folder.iterdir():
            if item.is_dir():
                yield from _traverse(item, prefix + item.name)

            else:
                aggregate = prefix + item.name.split('.')[0]
                m = re.search(r'([a-zA-Z0-9]{32})$', aggregate)
                if m is None:
                    raise RuntimeError("invalid path %r" % item)
                md5 = m.group(1).lower()
                assert len(md5) == 32
                yield (md5, item)

    ocr_root = Path(settings.MALDINI_OCR_ROOT) / tag
    for (md5, path) in _traverse(ocr_root):
        job = {
            'tag': tag,
            'md5': md5,
            'path': str(path.relative_to(ocr_root)),
        }
        queues.put('ocr', job, verbose=verbose)


def worker(tag, md5, path, verbose):
    ocr_root = Path(settings.MALDINI_OCR_ROOT) / tag

    row, created = models.Ocr.objects.get_or_create(tag=tag, md5=md5)
    if created:
        row.path = path
        with (ocr_root / path).open('rb') as f:
            row.text = pdftotext(f)
        row.save()
        if verbose: print(md5, 'add')

    else:
        if verbose: print(md5, 'skip')
