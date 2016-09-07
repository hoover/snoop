import re
from bs4 import BeautifulSoup, UnicodeDammit
import lxml.html
import lxml.html.clean
from lxml import etree

def _extract_links(html):
    tree = etree.fromstring(html, parser=etree.HTMLParser())

    url_index = []
    i = 0
    for link in tree.findall('.//a'):
        url = link.get('href')
        if url:
            i += 1
            index_data = {'title': link.text, 'url': url, 'id': i}

            link.tag = 'span'
            link.text = '{title} [{id}]'.format(**index_data)
            url_index.append(index_data)

    html = etree.tostring(tree, encoding="UTF-8", method='html')
    html = html.decode('utf-8')

    html += '<br/>\n<br/>\n'
    for index_data in url_index:
        html += '[{id}] {title}: \t {url} <br/>\n'.format(**index_data)

    return html

def _create_lxml_html_cleaner():
    # Consult http://lxml.de/3.4/api/lxml.html.clean.Cleaner-class.html
    cleaner = lxml.html.clean.Cleaner()

    # The idea here is to make it explicit to copy/paste a link, as all of our
    # links will be available as a text-only index.
    # Also remove any tags that would make inline printing bad, like <html>,
    # <head> and body.
    cleaner.remove_tags = ['a', 'img', 'head', 'html', 'body']

    # remove the shady stuff
    cleaner.javascript = True
    cleaner.scripts = True
    cleaner.links = True
    cleaner.embedded = True
    cleaner.frames = True

    # may contain exploits for IE6
    cleaner.comments = True
    cleaner.processing_instructions = True
    cleaner.meta = True
    cleaner.forms = True
    cleaner.remove_unknown_tags = True
    cleaner.annoying_tags = True

    # remove <style> so they don't propagate through to the rest of the page
    cleaner.style = True
    # keep inline styles, as they make the page more readable
    cleaner.inline_style = False

    return cleaner

lxml_cleaner = _create_lxml_html_cleaner()

def clean_html(html):
    dammit = UnicodeDammit(html, is_html=True)
    try:
        html = dammit.unicode_markup
    except ValueError:
        if isinstance(html, bytes):
            html = html.decode('latin-1')
        else:
            html = html

    # extract all links and move them to an index
    extracted_links = _extract_links(html)

    # clean the html using the default params
    clean = lxml.html.clean.clean_html(extracted_links)

    # paranoid: run another pass using our settings
    cleanest = lxml_cleaner.clean_html(clean)

    if not isinstance(cleanest, str):
        cleanest = lxml.html.tostring(cleanest, encoding='UTF-8')
    return cleanest

def text_from_html(html):
    soup = BeautifulSoup(html, 'lxml')
    for node in soup(["script", "style"]):
        node.extract()
    text = soup.get_text().strip()
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'[ \t\r\f\v]+', ' ', text)
    return text

def get_safe_html(doc):
    with doc.open() as f:
        return clean_html(f.read())
