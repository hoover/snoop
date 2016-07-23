import chardet
from .utils import text_from_html
from . import models

def decode_bytes(content):
    try:
        return content.decode('utf-8')

    except UnicodeDecodeError:
        encoding = chardet.detect(content)['encoding']
        if encoding:
            print("chardet guessed encoding", encoding)
            try:
                return content.decode(encoding)
            except UnicodeDecodeError:
                print("but even that failed")

        print("falling back to latin-1")
        return content.decode('latin-1')

@models.cache(models.HtmlTextCache, lambda doc: doc.id)
def get_text(doc):
    with doc.open() as f:
        content = f.read()
        if doc.content_type.startswith('text/html'):
            return text_from_html(content)
        else:
            return decode_bytes(content)
