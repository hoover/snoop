import chardet
from .html import text_from_html
from .content_types import guess_filetype
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

def get_text(doc):
    with doc.open() as f:
        content = f.read()
        if guess_filetype(doc) == 'html':
            return text_from_html(content)
        else:
            return decode_bytes(content)
