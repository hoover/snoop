import pytest
from django.conf import settings
from snoop import models, walker, views

skip_if_no_db = pytest.mark.skipif(not settings.DATABASES,
    reason="DATABASES not set")
pytestmark = [pytest.mark.django_db, skip_if_no_db]

@pytest.fixture
def collection():
    collection = models.Collection.objects.create(
        slug='apitest',
        path=settings.SNOOP_ROOT + '/eml-2-attachment',
    )
    walker.Walker.walk(
        root=collection.path,
        prefix=None,
        container_doc=None,
        collection=collection,
    )
    return collection

def test_get_data(collection):
    email = collection.document_set.get(path='message-without-subject.eml')
    data = views._process_document(collection.slug, email.id)
    content = data['data']
    assert content['date'] == '10 October 2013'
    assert content['type'] == 'email'
    assert content['filename'] == 'message-without-subject.eml'
    assert content['path'] == 'message-without-subject.eml'
    assert content['from'] == \
        'Negoita Camelia <don.t_mess_with_miky@yahoo.com>'
    assert content['md5'] == '2008f17802012f11fc4b35234a4af672'
