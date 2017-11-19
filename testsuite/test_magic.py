from pathlib import Path
import pytest
from django.conf import settings
from snoop import magic
from snoop.utils import chunks

root = Path(settings.SNOOP_ROOT)


@pytest.mark.parametrize('path,mime_type,mime_encoding', [
    ('words/usr-share-dict-words.txt', 'text/plain', 'utf-8'),
])
def test_magic(path, mime_type, mime_encoding):
    m = magic.Magic()
    with (root / path).open('rb') as f:
        for buffer in chunks(f):
            m.update(buffer)
    assert m.get_result() == (mime_type, mime_encoding)
