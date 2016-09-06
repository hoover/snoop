import re
from bs4 import BeautifulSoup, UnicodeDammit
import lxml.html
import lxml.html.clean
import lxml.etree


def _extract_links(html):
    from lxml.etree import fromstring, tostring, HTMLParser

    tree = fromstring(html, parser=HTMLParser())

    url_index = []
    i = 0
    for link in tree.findall('.//a'):
        title = link.text
        url = link.get('href')
        if url:
            i += 1
            link.tag = 'span'
            link.text = '%s [%s]' % (link.text, i)
            url_index.append({'title': title, 'url': url})

    html = tostring(tree, encoding="UTF-8", method='html').decode('utf-8')
    print(type(html))
    for i, link in enumerate(url_index):
        if i == 0:
            html += '<br/>\n<br/>\n'
        html += '[%s] %s: \t %s <br/>\n' % (i + 1, link['title'], link['url'])
    return html


def _create_lxml_html_cleaner():
    cleaner = lxml.html.clean.Cleaner()

    # Only the tags will be removed, their content will get pulled up into
    # the parent tag. The idea here is to make it explicit to copy/paste a link
    # Also remove any tags that would make inline printing bad (html, head, body)
    cleaner.remove_tags = ['a', 'img', 'head', 'html', 'body']

    # removes all javascript, like onclick=
    cleaner.javascript = True
    # removes <script>s
    cleaner.scripts = True
    # removes <link>s
    cleaner.links = True
    # removes flash, iframes
    cleaner.embedded = True
    cleaner.frames = True

    # removes <blink> and <marquee>
    cleaner.annoying_tags = True

    # may contain exploits for IE6
    cleaner.comments = True
    cleaner.processing_instructions = True
    cleaner.meta = True
    cleaner.forms = True
    cleaner.remove_unknown_tags = True

    # remove <style> so they don't propagate through to the rest of the page
    cleaner.style = True
    # keep inline styles, as they make the page more readable
    cleaner.inline_style = False

    return cleaner

LXML_CLEANER = _create_lxml_html_cleaner()


def clean_html(html):
    dammit = UnicodeDammit(html, is_html=True)
    try:
        doc = dammit.unicode_markup
    except ValueError:
        if type(html) is bytes:
            doc = html.decode('latin-1')
        else:
            doc = html

    # extract all links and move them to an index
    extracted_links = _extract_links(doc)

    # clean the html using the default params
    clean = lxml.html.clean.clean_html(extracted_links)

    # paranoid: run another pass using our settings
    cleanest = LXML_CLEANER.clean_html(clean)

    if type(cleanest) is not str:
        cleaner = lxml.html.tostring(cleanest, encoding='UTF-8')
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
