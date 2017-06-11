from . import models
from .walker import FOLDER

def create_collection(slug, path, es_index='', title='', description=''):
    collection = models.Collection.objects.create(
        slug=slug,
        path=path,
        es_index=es_index,
        title=title,
        description=description,
    )
    models.Document.objects.get_or_create(
        path='',
        disk_size=0,
        content_type=FOLDER,
        filename='',
        collection=collection,
    )
    return collection
