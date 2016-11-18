import pytest
from django.conf import settings
from snoop import models, walker, views

skip_if_no_db = pytest.mark.skipif(not settings.DATABASES,
    reason="DATABASES not set")
pytestmark = [pytest.mark.django_db, skip_if_no_db]

@pytest.fixture
def testdata():
    testdata = models.Collection.objects.create(
        slug='apitest',
        path=settings.SNOOP_ROOT + '/eml-2-attachment',
    )
    walker.Walker.walk(
        root=testdata.path,
        prefix=None,
        container_doc=None,
        collection=testdata,
    )
    return testdata

def test_get_data(testdata):
    email = testdata.document_set.get(path='message-without-subject.eml')
    data = views._process_document(testdata.slug, email.id)
    content = data['content']
    assert content['date'] == '10 October 2013'
    assert content['type'] == 'email'
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
