from pathlib import Path
from collections import defaultdict
import re
from django.conf import settings
from . import models
from .utils import pdftotext

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

    assert settings.MALDINI_OCR_ROOT is not None
    ocr_root = Path(settings.MALDINI_OCR_ROOT)
    counters = defaultdict(int)

    for (md5, path) in _traverse(ocr_root / tag):
        row, created = models.Ocr.objects.get_or_create(tag=tag, md5=md5)
        if created:
            row.path = str(path)
            with path.open('rb') as f:
                row.text = pdftotext(f)
            row.save()
            counters['added'] += 1
            if verbose: print(md5)

        else:
            counters['skipped'] += 1

    if verbose: print(dict(counters))