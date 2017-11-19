import hashlib
from pathlib import Path
import pytest
from django.conf import settings
from django.test.utils import override_settings
from snoop import models
from snoop.utils import chunks
from snoop.magic import Magic
from snoop import archives

pytestmark = pytest.mark.django_db

WORDS_MD5 = 'cbbcded3dc3b61ad50c4e36f79c37084'
WORDS_SHA1 = '33a07ef770a51b476e5a480b2dc3628c3b939395'
WORDS_SHA3_256 = ('5490ccb75c33798427f7e746150e74f1'
                  '816da0449dd9c40a7f741f039d16d6cc')

MOUSE_SHA1 = 'dd0c5fad4180f3ae71aa401285b803b9434deac6'

container_cache = Path(settings.SNOOP_CONTAINER_CACHE)


def walk_children(doc, path):
    children = {c.filename_bytes: c for c in doc.child_set.all()}
    for item in path.iterdir():
        filename_bytes = item.name.encode('utf8')
        child = children.get(filename_bytes)
        if child is None:
            child = doc.child_set.create(
                collection=doc.collection,
                filename_bytes=filename_bytes,
            )
        walk(child, path / child.filename)


def make_blob(doc, path):
    hashes = {
        'md5': hashlib.md5(),
        'sha1': hashlib.sha1(),
        'sha3_256': hashlib.sha3_256(),
    }
    magic = Magic()

    blob_storage = models.FlatBlobStorage(settings.SNOOP_BLOB_STORAGE)
    with blob_storage.save() as b:
        with path.open('rb') as f:
            size = 0
            for block in chunks(f):
                size += len(block)
                for h in hashes.values():
                    h.update(block)
                magic.update(block)
                b.write(block)

        digest = {name: hash.hexdigest() for name, hash in hashes.items()}
        b.set_filename(digest['sha3_256'])

    fields = dict(digest)
    fields['size'] = size
    (fields['mime_type'], fields['mime_encoding']) = magic.get_result()

    blob, _ = models.Blob.objects.get_or_create(
        sha3_256=fields['sha3_256'],
        defaults=fields,
    )
    doc.blob = blob
    doc.save()


def walk(doc, path):
    if path.is_file():
        if doc.blob is None:
            make_blob(doc, path)

    if path.is_dir():
        walk_children(doc, path)

    elif doc.blob.mime_type in archives.KNOWN_TYPES:
        cache = container_cache / doc.blob.sha3_256
        if not cache.exists():
            cache.mkdir()
            try:
                archives.call_7z(str(path), str(cache))
            except (archives.EncryptedArchiveFile, archives.ExtractingFailed):
                return
        walk_children(doc, cache)


def lookup(col, path):
    doc = None

    for name in path.split('/'):
        for child in col.document_set.filter(parent=doc):
            if child.filename == name:
                break
        else:
            raise RuntimeError(f'not found: {name} in {doc}')
        doc = child

    return doc


@pytest.fixture
def mock_blob_storage(tmpdir):
    with override_settings():
        settings.SNOOP_BLOB_STORAGE = str(tmpdir.mkdir('blob_storage'))
        yield


def test_walk_testdata(mock_blob_storage):
    col = models.Collection.objects.create(
        name='testdata',
        path=settings.SNOOP_ROOT,
    )
    walk(col.get_root(), Path(col.path))

    words = lookup(col, '/words/usr-share-dict-words.txt')
    assert words.filename == 'usr-share-dict-words.txt'
    assert words.blob.md5 == WORDS_MD5
    assert words.blob.sha1 == WORDS_SHA1
    assert words.blob.sha3_256 == WORDS_SHA3_256
    assert words.blob.mime_type == 'text/plain'
    assert words.blob.mime_encoding == 'utf-8'

    with words.blob.open() as f:
        assert hashlib.sha1(f.read()).hexdigest() == WORDS_SHA1

    mouse = lookup(col, '/disk-files/archives/tim-and-merry'
        '/archives.zip/jerry/etc/jerry.7z/mouse'
        '/stock-photo-house-mouse-standing'
        '-on-rear-feet-mus-musculus-137911070.jpg')
    assert mouse.blob.sha1 == MOUSE_SHA1

    with mouse.blob.open() as f:
        assert hashlib.sha1(f.read()).hexdigest() == MOUSE_SHA1
