import pytest
from django.conf import settings
from snoop import models

@pytest.fixture
def document_collection():
    collection = models.Collection(
        path=settings.SNOOP_ROOT,
        slug='dummy',
        title='dummy collection title',
        es_index='dummy',
        description='This collection is used for testing.',
    )
    return collection
