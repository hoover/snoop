from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urljoin
import pytest
from django.conf import settings
from snoop import models, walker, views

pytestmark = [
    pytest.mark.django_db,
    pytest.mark.skipif(not settings.DATABASES, reason="DATABASES not set"),
    pytest.mark.skip("Model refactoring"),
]

def _collection(**kwargs):
    col = models.Collection.objects.create(**kwargs)
    walker.Walker.walk(
        root=col.path,
        prefix=None,
        container_doc=None,
        collection=col,
    )
    return col

@pytest.fixture
def testdata():
    return _collection(
        slug='apitest',
        path=settings.SNOOP_ROOT + '/eml-2-attachment',
    )

def test_get_data(testdata):
    email = testdata.document_set.get(path='message-without-subject.eml')
    data = views._process_document(testdata.slug, email.id)
    content = data['content']
    assert content['date'] == '2013-10-10T10:04:49-07:00'
    assert content['filetype'] == 'email'
    assert content['filename'] == 'message-without-subject.eml'
    assert content['path'] == 'message-without-subject.eml'
    assert content['from'] == \
        'Negoita Camelia <don.t_mess_with_miky@yahoo.com>'
    assert content['md5'] == '2008f17802012f11fc4b35234a4af672'

def test_attachments(testdata):
    from snoop.digest import create_children, digest
    email = testdata.document_set.get(path='message-without-subject.eml')
    new_children = create_children(email, digest(email), True)
    data = views._process_document(testdata.slug, email.id)
    children = data['children']
    assert len(children) == 2
    assert children[0]['filename'] == 'IMAG1077.jpg'
    assert children[0]['content_type'] == 'image/jpeg'

@pytest.fixture
def mockdata():
    with TemporaryDirectory() as tmp:
        root = Path(tmp) / 'mock'
        root.mkdir()
        for n in range(42):
            with (root / 'doc_{}.txt'.format(n)).open('w') as f: pass
        col = _collection(slug='mock', path=str(root), title="Mock")
        from snoop.digest import worker
        for doc in col.document_set.all():
            worker(doc.id, False)
        yield col

def test_collection_metadata_and_feed(mockdata, client):
    col_url = '/mock/json'
    col = client.get(col_url).json()
    assert col['title'] == "Mock"

    def feed_page(url):
        page = client.get(url).json()
        next_url = urljoin(url, page['next']) if page.get('next') else None
        return next_url, page['documents']

    docs = []
    feed_url = urljoin(col_url, col['feed'])
    while feed_url:
        feed_url, page_docs = feed_page(feed_url)
        docs.extend(page_docs)

    expected_paths = {''} ^ {"doc_{}.txt".format(n) for n in range(42)}
    assert {d['content']['path'] for d in docs} == expected_paths
