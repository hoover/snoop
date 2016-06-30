import mimetypes
from maldini import digest, models

# TODO
# - guess_filetype: various extensions and content-types (to be discovered on the field)
# - errors: corrupt docs, missing docs

PATH_TEXT = "disk-files/pdf-doc-txt/easychair.txt"
PATH_HTML = "disk-files/bad-html/alert.html"

models.Ocr.objects.filter = lambda *a, **k: []
models.Ocr.objects.all = lambda *a, **k: []

def digest_path(path):
    content_type = mimetypes.guess_type(path, False)[0]
    filename = path.split('/')[-1]
    doc = models.Document(path=path,
                          content_type=content_type,
                          filename=filename)
    doc.save = lambda: None
    return digest.digest(doc)

def test_hashes_path_filetype():
    data = digest_path(PATH_TEXT)

    assert "disk-files/pdf-doc-txt/easychair.txt" == data['path']
    assert "easychair.txt" == data['filename']
    assert "text" == data['type']
    assert "840c68eb114c659ee4934eb14df0e499" == data['md5']
    assert "58151db60c6a7e83628cbd9bdff0312763872a3c" == data['sha1']

def test_text():
    data = digest_path(PATH_TEXT)

    assert "text" == data['type']
    assert "styles and parameters" in data['text']
    assert "serving thousands of conferences every year" in data['text']


def test_html_text():
    data = digest_path(PATH_HTML)

    assert 'html' == data['type']
    assert "HAHAHAHAH" in data['text']

