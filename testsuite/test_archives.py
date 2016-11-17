import pytest
import shutil
from pathlib import Path
import tempfile
from django.conf import settings
from snoop import digest, models, archives
from snoop.content_types import guess_content_type

pytestmark = pytest.mark.skipif(not settings.SNOOP_SEVENZIP_BINARY,
    reason="SNOOP_SEVENZIP_BINARY not set")

ZIP_SIMPLE = {
    'parent': None,
    'path': "disk-files/archives/zip-with-docx-and-doc.zip",
    'files': [
        "AppBody-Sample-English.docx",
        "sample.doc"
    ],
    'sha1': 'f7bafa8f401d5327cd69423ba83cdac3b6e6b945',
    'filename': 'zip-with-docx-and-doc.zip',
    'type': 'archive',
}

RAR_SIMPLE = {
    'parent': None,
    'path': "disk-files/archives/rar-with-pdf-doc-docx.rar",
    'files': [
        "sample (1).doc",
        "Sample_BulletsAndNumberings.docx",
        "cap33.pdf"
    ],
    'md5': '0aa545beed4b0b7bc2b16bc87eebeff9',
    'filename': 'rar-with-pdf-doc-docx.rar',
    'type': 'archive',
}

EML_SIMPLE = {
    'parent': None,
    'path': "eml-2-attachment/Urăsc canicula, e nașpa.eml",
    'type': 'email',
}

ZIP_ATTACHMENT = {
    'parent': EML_SIMPLE,
    'path': '3',
    'filename': 'zip-with-pdf.zip',
    'files': [
        'cap33.pdf'
    ],
    'sha1': 'cb191b36eee4b6b3a9db58199ff2bad61af2f635',
    'type': 'archive',
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
        monkeypatch.setattr(archives, 'CACHE_ROOT', Path(tmp))
        yield

def doc_obj(obj, collection):
    filename = obj.get('filename') or obj['path'].split('/')[-1]
    content_type = guess_content_type(filename)
    doc = models.Document(path=obj['path'],
                          content_type=content_type,
                          filename=filename,
                          collection=collection)
    doc.save = lambda *a, **k: None
    if obj.get('sha1'):
        doc.sha1 = obj['sha1']
    if obj.get('parent'):
        doc.container = doc_obj(obj['parent'], collection)
    return doc

def digest_obj(obj, collection):
    return digest.digest(doc_obj(obj, collection))

def assert_archive_consistence(obj, collection):
    data = digest_obj(obj, collection)
    keys = ['filename', 'sha1', 'md5', 'type', 'text']
    for key in keys:
        if key in obj:
            assert obj[key] == data[key]

def test_simple_zip_archive(document_collection):
    assert_archive_consistence(ZIP_SIMPLE, document_collection)

def test_simple_rar_archive(document_collection):
    assert_archive_consistence(RAR_SIMPLE, document_collection)

def test_zip_attachment(document_collection):
    assert_archive_consistence(ZIP_ATTACHMENT, document_collection)

SEVENZ = {
    "parent": None,
    "path": "eml-7-recursive/d.7z",
    'files': ['this/is/deep/recursivitate.eml'],
    'sha1': 'f5fc5a8221cff1f5a621bac4d46ebaf44acdd08a',
    'type': 'archive',
}

SEVENZ_EMAIL = {
    'parent': SEVENZ,
    'path': "this/is/deep/recursivitate.eml",
    'sha1': '0e366a509c4eb2232375fa7488259fbd261618db',
    'type': 'email',
}

SEVENZ_EMAIL_ZIP = {
    'parent': SEVENZ_EMAIL,
    'path': '3',
    'filename': 'a.zip',
    'type': 'archive',
    'sha1': '3ac46acf315c3d24d7d3577a66fd94e93992dcfe',
}

SEVENZ_EMAIL_ZIP_FILE = {
    'parent': SEVENZ_EMAIL_ZIP,
    'path': 'a/b/c.txt',
    'type': 'text',
    'text': 'GET OUT OF MY LIFE, JILL\n\n',
}

def test_complex_container_structure(document_collection):
    assert_archive_consistence(SEVENZ, document_collection)
    assert_archive_consistence(SEVENZ_EMAIL, document_collection)
    assert_archive_consistence(SEVENZ_EMAIL_ZIP, document_collection)
    assert_archive_consistence(SEVENZ_EMAIL_ZIP_FILE, document_collection)

ZIP_WITH_MSG = {
    "parent": None,
    "path": "msg-5-outlook/archive-with-msg.zip",
    "filename": "archive-with-msg.zip",
    "files": ["the-same-thing-zipped.msg"],
    "sha1": "757028691204560f1e7ec2b9eabcdb1a35e364d9",
}

MSG_IN_ZIP = {
    "parent": ZIP_WITH_MSG,
    "path": "the-same-thing-zipped.msg",
    "filename": "the-same-thing-zipped.msg",
    "type": "email",
    "md5": "38385c4487719fa9dd0fb695d3aad0ee",
}

def test_msg_inside_container(document_collection):
    assert_archive_consistence(ZIP_WITH_MSG, document_collection)
    assert_archive_consistence(MSG_IN_ZIP, document_collection)
