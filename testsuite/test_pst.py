import pytest
from pathlib import Path
import tempfile
from django.conf import settings
from snoop import digest, models, pst
from snoop.content_types import guess_content_type

pytestmark = pytest.mark.skipif(not settings.SNOOP_READPST_BINARY,
    reason="SNOOP_READPST_BINARY not set")

PST_JANE_AND_DOE = {
    'parent': None,
    'path': "pst/flags_jane_doe.pst",
    'files': [
        "pst-test-2@aranetic.com/5.eml",
        "pst-test-2@aranetic.com/Inbox/1.eml",
        "pst-test-2@aranetic.com/Inbox/2.eml",
        "pst-test-2@aranetic.com/Inbox/3.eml",
        "pst-test-2@aranetic.com/Inbox/4.eml",
        "pst-test-2@aranetic.com/Inbox/5.eml",
        "pst-test-2@aranetic.com/Inbox/6.eml",
        "pst-test-2@aranetic.com/Sent Items/1.eml",
        "pst-test-2@aranetic.com/Sent Items/2.eml",
    ],
    'md5': '699502e6b8c005e0f2b3d523cf9479cc',
    'sha1': '7638280179f243ad10fcb4cd651bbfb5d979f5ab',
    'filename': 'flags_jane_doe.pst',
    'type': 'email-archive',
}

EMAIL_TWO = {
    'parent': PST_JANE_AND_DOE,
    'path': 'pst-test-2@aranetic.com/Inbox/2.eml',
    'md5': '46e5c10ee1603086e6fcf20acc4d1581',
    'sha1': '23e41ddfb84491bfc593fc7cc9d4b76b5a15e130',
    'type': 'email',
}

@pytest.fixture(autouse=True)
def no_models(monkeypatch):
    def disable(item, attr, default):
        def dummy(*a, **k):
            return default
        monkeypatch.setattr(item, attr, dummy)
    class DummyDocument:
        id = 0
    disable(models.Ocr.objects, 'filter', [])
    disable(models.Ocr.objects, 'all', [])
    disable(models.Document.objects, 'get_or_create', (DummyDocument(), False))

@pytest.yield_fixture(autouse=True)
def archive_dir(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setattr(pst, 'CACHE_ROOT', Path(tmp))
        yield

def doc_obj(obj, collection):
    filename = obj.get('filename') or obj['path'].split('/')[-1]
    content_type = guess_content_type(filename)
    doc = models.Document(
        path=obj['path'],
        content_type=content_type,
        filename=filename,
        collection=collection,
    )
    doc.save = lambda *a, **k: None
    if obj.get('sha1'):
        doc.sha1 = obj['sha1']
    if obj.get('md5'):
        doc.md5 = obj['md5']
    if obj.get('parent'):
        doc.container = doc_obj(obj['parent'], collection)
    return doc

def digest_obj(obj, collection):
    return digest.digest(doc_obj(obj, collection))

def assert_archive_consistence(obj, collection):
    data = digest_obj(obj, collection)
    print(data)
    keys = ['filename', 'sha1', 'md5', 'type', 'text']
    for key in keys:
        if key in obj:
            assert obj[key] == data[key]

@pytest.mark.skip
def test_simple_pst_data(document_collection):
    assert_archive_consistence(PST_JANE_AND_DOE, document_collection)
    assert_archive_consistence(EMAIL_TWO, document_collection)

@pytest.mark.skip
def test_pst_email(document_collection):
    data = digest_obj(EMAIL_TWO, document_collection)
    assert "This email has never been read." in data['text']
