from pathlib import Path
import re
from . import models
from .content_types import guess_content_type

FOLDER = 'application/x-directory'

class Walker(object):

    def __init__(self, root, prefix, restart, container_doc):
        self.root = Path(root)
        self.prefix = Path(prefix) if prefix else None
        self.container_doc = container_doc
        self.documents = []
        if restart:
            models.FolderMark.objects.all().delete()

    @classmethod
    def walk(cls, *args):
        self = cls(*args)
        try:
            first_item = self.root / self.prefix if self.prefix else self.root
            first_parent = self.container_doc
            self.handle(first_item, first_parent)
        except KeyboardInterrupt:
            pass
        return self.documents

    def _path(self, file):
        return file.relative_to(self.root)

    def handle(self, item, parent):
        if item.is_dir():
            self.handle_folder(item, parent)
        else:
            self.handle_file(item, parent)

    def handle_folder(self, folder, parent):
        path = self._path(folder)
        if str(path) == '.':
            if self.container_doc:
                new_doc = self.container_doc
            else:
                new_doc, _ = models.Document.objects.get_or_create(
                    path='',
                    disk_size=0,
                    content_type=FOLDER,
                    filename='',
                )
        else:
            new_doc, created = models.Document.objects.get_or_create(
                path=path,
                disk_size=0,
                content_type=FOLDER,
                filename=path.name,
                parent=parent,
                container=self.container_doc,
            )
            self.documents.append((new_doc, created))
        for child in folder.iterdir():
            self.handle(child, new_doc)

    def handle_file(self, file, parent):
        path = self._path(file)
        new_doc, created = models.Document.objects.get_or_create(
            path=path,
            parent=parent,
            container=self.container_doc,
            defaults={
                'disk_size': file.stat().st_size,
                'content_type': guess_content_type(file.name),
                'filename': path.name,
            },
        )
        self.documents.append((new_doc, created))

def files_in(parent_path):
    child_documents = models.Document.objects.filter(
        container=None,
        path__iregex=r'^' + re.escape(parent_path) + r'[^/]+$',
    )
    return [{
        'id': child.id,
        'filename': child.path[len(parent_path):],
        'size': child.disk_size,
        'content_type': child.content_type,
    } for child in child_documents]

def _fix_mimetypes():
    for doc in models.Document.objects.iterator():
        if doc.content_type:
            lower_content_type = doc.content_type.lower()
            if doc.content_type != lower_content_type:
                print('lowercasing', doc.id, doc.content_type)
                doc.content_type = lower_content_type
                doc.save()

        else:
            if doc.container_id is None:
                content_type = guess_content_type(Path(doc.path).name)
                if content_type:
                    print('adding', doc.id, content_type)
                    doc.content_type = content_type
                    doc.save()
