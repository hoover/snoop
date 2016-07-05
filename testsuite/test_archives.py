import pytest
import shutil
from pathlib import Path
from django.conf import settings
from maldini import digest, models
from maldini.content_types import guess_content_type

CACHE_ROOT = Path(settings.ARCHIVE_CACHE_ROOT)


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
def no_ocr_models(monkeypatch):
    func_empty_list = lambda *a, **k: []
    monkeypatch.setattr(models.Ocr.objects, "filter", func_empty_list)
    monkeypatch.setattr(models.Ocr.objects, "all", func_empty_list)

@pytest.fixture(autouse=True)
def clean_archive_dir():
    if CACHE_ROOT.is_dir():
        shutil.rmtree(str(CACHE_ROOT))
    CACHE_ROOT.mkdir()

def doc_obj(obj):
    filename = obj.get('filename') or obj['path'].split('/')[-1]
    content_type = guess_content_type(filename)
    doc = models.Document(path=obj['path'],
                          content_type=content_type,
                          filename=filename)
    doc.save = lambda *a, **k: None
    if obj.get('sha1'):
        doc.sha1 = obj['sha1']
    if obj.get('parent'):
        doc.container = doc_obj(obj['parent'])
    return doc

def digest_obj(obj):
    return digest.digest(doc_obj(obj))

def assert_archive_consistence(obj):
    data = digest_obj(obj)
    keys = ['filename', 'sha1', 'md5', 'type', 'text']
    for key in keys:
        if key in obj:
            assert obj[key] == data[key]

    if 'files' in obj:
        assert set(obj['files']) == set(data['file_list'])


def test_simple_zip_archive():
    assert_archive_consistence(ZIP_SIMPLE)

def test_simple_rar_archive():
    assert_archive_consistence(RAR_SIMPLE)

def test_zip_attachment():
    assert_archive_consistence(ZIP_ATTACHMENT)

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

def test_complex_container_structure():
    assert_archive_consistence(SEVENZ)
    assert_archive_consistence(SEVENZ_EMAIL)
    assert_archive_consistence(SEVENZ_EMAIL_ZIP)
    assert_archive_consistence(SEVENZ_EMAIL_ZIP_FILE)
