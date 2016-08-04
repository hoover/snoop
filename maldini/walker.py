from pathlib import Path
import re
from . import models
from .content_types import guess_content_type

FOLDER = 'application/x-directory'

class Walker(object):

    def __init__(self, generation, root, prefix, restart):
        self.generation = generation
        self.root = Path(root)
        self.prefix = Path(prefix) if prefix else None
        if restart:
            models.FolderMark.objects.all().delete()


    @classmethod
    def walk(cls, *args):
        self = cls(*args)
        try:
            return self.handle(self.root / self.prefix if self.prefix else None)
        except KeyboardInterrupt:
            pass

    def _path(self, file):
        return file.relative_to(self.root)

    def handle(self, item=None):
        if item is None:
            item = self.root

        if item.is_dir():
            self.handle_folder(item)

        else:
            self.handle_file(item)

    def handle_folder(self, folder):
        path = self._path(folder)
        print('FOLDER', path)
        if models.FolderMark.objects.filter(path=path).count():
            print('SKIP', path)
            return
        if str(path) != '.':
            models.Document.objects.get_or_create(
                path=path,
                disk_size=0,
                content_type=FOLDER,
                filename=path.name,
            )
        for child in folder.iterdir():
            self.handle(child)
        models.FolderMark.objects.create(path=path)
        print('MARK', path)

    def handle_file(self, file):
        path = self._path(file)
        print('FILE', path)
        models.Document.objects.get_or_create(path=path, defaults={
            'disk_size': file.stat().st_size,
            'content_type': guess_content_type(file.name),
            'filename': path.name,
        })

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
