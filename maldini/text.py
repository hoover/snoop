from .utils import text_from_html

def get_text(doc):
    with doc.open() as f:
        content = f.read()
        if doc.content_type.startswith('text/html'):
            return text_from_html(content)
        else:
            return content.decode('utf-8')
