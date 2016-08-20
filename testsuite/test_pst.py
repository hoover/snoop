import pytest
from pathlib import Path
import tempfile
from snoop import digest, models, pst
from snoop.content_types import guess_content_type

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
def no_ocr_models(monkeypatch):
    func_empty_list = lambda *a, **k: []
    monkeypatch.setattr(models.Ocr.objects, "filter", func_empty_list)
    monkeypatch.setattr(models.Ocr.objects, "all", func_empty_list)

@pytest.yield_fixture(autouse=True)
def archive_dir(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setattr(pst, 'CACHE_ROOT', Path(tmp))
        yield

def doc_obj(obj):
    filename = obj.get('filename') or obj['path'].split('/')[-1]
    content_type = guess_content_type(filename)
    doc = models.Document(path=obj['path'],
                          content_type=content_type,
                          filename=filename)
    doc.save = lambda *a, **k: None
    if obj.get('sha1'):
        doc.sha1 = obj['sha1']
    if obj.get('md5'):
        doc.md5 = obj['md5']
    if obj.get('parent'):
        doc.container = doc_obj(obj['parent'])
    return doc

def digest_obj(obj):
    return digest.digest(doc_obj(obj))

def assert_archive_consistence(obj):
    data = digest_obj(obj)
    print(data)
    keys = ['filename', 'sha1', 'md5', 'type', 'text']
    for key in keys:
        if key in obj:
            assert obj[key] == data[key]

    if 'files' in obj:
        assert set(obj['files']) == set(data['file_list'])


def test_simple_pst_data():
    assert_archive_consistence(PST_JANE_AND_DOE)
    assert_archive_consistence(EMAIL_TWO)

def test_pst_email():
    data = digest_obj(EMAIL_TWO)
    assert "This email has never been read." in data['text']
