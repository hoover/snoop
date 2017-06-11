from pathlib import Path
from . import models
from . import walker
from .content_types import guess_content_type

def is_folder(doc):
    return doc.content_type == walker.FOLDER

def list_children(folder):
    if folder.container:
        # assume that walking is already done
        return []

    collection_path = Path(folder.collection.path)
    folder_path = collection_path / folder.path

    rv = []
    for item in folder_path.iterdir():
        if item.is_dir():
            new_doc, created = models.Document.objects.get_or_create(
                path=item.relative_to(collection_path),
                disk_size=0,
                content_type=walker.FOLDER,
                filename=item.name,
                parent=folder,
                container=folder.container,
                collection=folder.collection,
            )
            rv.append((new_doc.id, created))

        else:
            new_doc, created = models.Document.objects.get_or_create(
                path=item.relative_to(collection_path),
                parent=folder,
                container=folder.container,
                collection=folder.collection,
                defaults={
                    'disk_size': item.stat().st_size,
                    'content_type': guess_content_type(item.name),
                    'filename': item.name,
                },
            )
            rv.append((new_doc.id, created))

    return rv
