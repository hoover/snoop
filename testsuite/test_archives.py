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
}

RAR_SIMPLE = {
    'parent': None,
    'path': "disk-files/archives/rar-with-pdf-doc-docx.rar",
    'files': [
        "sample (1).doc",
        "Sample_BulletsAndNumberings.docx",
        "cap33.pdf"
    ],
}

EML_SIMPLE = {
    'parent': None,
    'path': "eml-2-attachment/Urăsc canicula, e nașpa.eml",
    'files': [
        '?'
    ],
}

ZIP_ATTACHMENT = {
    'parent': EML_SIMPLE,
    'path': '3',
    'filename': 'zip-with-pdf.zip',
    'files': [
        'cap33.pdf'
    ],
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
    if obj['parent']:
        doc.container = doc_obj(obj['parent'])
    return doc

def digest_obj(obj):
    return digest.digest(doc_obj(obj))

def test_simple_zip_archive():
    data = digest_obj(ZIP_SIMPLE)

    assert 'archive' == data.get('type')
    assert set(ZIP_SIMPLE['files']) == set(data.get('file_list'))
    assert 'zip-with-docx-and-doc.zip' == data.get('filename')
    assert 'f7bafa8f401d5327cd69423ba83cdac3b6e6b945' == data.get('sha1')

def test_simple_rar_archive():
    data = digest_obj(RAR_SIMPLE)

    assert 'archive' == data.get('type')
    assert set(RAR_SIMPLE['files']) == set(data.get('file_list'))
    assert '0aa545beed4b0b7bc2b16bc87eebeff9' == data.get('md5')
    assert 'rar-with-pdf-doc-docx.rar' == data.get('filename')

def test_zip_attachment():
    data = digest_obj(ZIP_ATTACHMENT)

    assert 'archive' == data.get('type')
    assert set(ZIP_ATTACHMENT['files']) == set(data.get('file_list'))
    assert 'cb191b36eee4b6b3a9db58199ff2bad61af2f635'  == data.get('sha1')
    assert 'zip-with-pdf.zip' == data.get('filename')
