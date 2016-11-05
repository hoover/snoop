import pytest
from snoop import digest, models
from snoop.content_types import guess_content_type

PATH_TEXT = "disk-files/pdf-doc-txt/easychair.txt"
PATH_HTML = "disk-files/bad-html/alert.html"
PATH_IMAGE = 'disk-files/images/bikes.jpg'

@pytest.fixture(autouse=True)
def no_ocr_models(monkeypatch):
    func_empty_list = lambda *a, **k: []
    monkeypatch.setattr(models.Ocr.objects, "filter", func_empty_list)
    monkeypatch.setattr(models.Ocr.objects, "all", func_empty_list)

def digest_path(path, collection):
    content_type = guess_content_type(path)
    filename = path.split('/')[-1]
    doc = models.Document(
        path=path,
        content_type=content_type,
        filename=filename,
        collection=collection,
    )
    doc.save = lambda: None
    return digest.digest(doc)

def test_hashes_path_filetype(document_collection):
    data = digest_path(PATH_TEXT, document_collection)

    assert "disk-files/pdf-doc-txt/easychair.txt" == data['path']
    assert "easychair.txt" == data['filename']
    assert "text" == data['type']
    assert "840c68eb114c659ee4934eb14df0e499" == data['md5']
    assert "58151db60c6a7e83628cbd9bdff0312763872a3c" == data['sha1']

def test_text(document_collection):
    data = digest_path(PATH_TEXT, document_collection)

    assert "text" == data['type']
    assert "styles and parameters" in data['text']
    assert "serving thousands of conferences every year" in data['text']
    assert data['word-count'] == 72

def test_html_text(document_collection):
    data = digest_path(PATH_HTML, document_collection)

    assert 'html' == data['type']
    assert "HAHAHAHAH" in data['text']
    assert "more text" in data['text']
    assert data['word-count'] == 5

def test_digest_image_exif(document_collection):
    data = digest_path(PATH_IMAGE, document_collection)

    assert data['location'] == '33.87546081542969, -116.3016196017795'
    assert data['date-created'] == '2006-02-11T11:06:37'
