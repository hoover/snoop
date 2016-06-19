from pathlib import Path
import mimetypes
import re
from . import models

mimetypes.add_type('message/x-emlx', '.emlx')
mimetypes.add_type('message/x-emlxpart', '.emlxpart')

def mime_type(name):
    return mimetypes.guess_type(name, strict=False)[0]

class Walker(object):

    def __init__(self, generation, root, prefix):
        self.generation = generation
        self.root = Path(root)
        self.prefix = Path(prefix) if prefix else None


    @classmethod
    def walk(cls, *args):
        self = cls(*args)
        try:
            return self.handle(self.root / self.prefix if self.prefix else None)
        except KeyboardInterrupt:
            pass

    def _path(self, file):
        return file.relative_to(self.root)

    def handle(self, file=None):
        if file is None:
            file = self.root

        if file.is_dir():
            path = self._path(file)
            if models.FolderMark.objects.filter(path=path).count():
                print('SKIP', path)
                return
            for child in file.iterdir():
                self.handle(child)
            models.FolderMark.objects.create(path=path)
            print('MARK', path)

        else:
            self.handle_file(file)

    def handle_file(self, file):
        path = self._path(file)
        print('FILE', path)
        doc, _ = models.Document.objects.get_or_create(path=path, defaults={
            'disk_size': file.stat().st_size,
            'content_type': mime_type(file.name) or '',
            'filename': path.name,
        })
        doc.save()

def files_in(parent_path):
    child_documents = models.Document.objects.filter(
        container=None,
        path__iregex=r'^' + re.escape(parent_path) + r'[^/]+$',
    )
    return [{
        'id': child.id,
        'filename': child.path[len(parent_path):]
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
                content_type = mime_type(Path(doc.path).name)
                if content_type:
                    print('adding', doc.id, content_type)
                    doc.content_type = content_type
                    doc.save()
