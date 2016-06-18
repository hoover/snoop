from pathlib import Path
from . import models

class Walker(object):

    def __init__(self, generation, root, prefix):
        self.generation = generation
        self.root = Path(root)
        self.prefix = Path(prefix) if prefix else None


    @classmethod
    def walk(cls, *args):
        self = cls(*args)
        self.processed = 0
        self.exceptions = 0
        self.uncommitted = 0

        try:
            return self.handle(self.root / self.prefix if self.prefix else None)
        except KeyboardInterrupt:
            pass

        # TODO commit
        return self.processed, self.exceptions

    def _path(self, file):
        return str(file.relative_to(self.root))

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
        doc, _ = models.Document.objects.get_or_create(path=path, defaults={'disk_size': file.stat().st_size})
        doc.save()

        #if file.suffixes[-1:] == ['.emlx']:
        #    self.handle_emlx(file)

    def handle_emlx(self, file):
        path = unicode(file.relative_to(self.root))
        row = (
            self.session
            .query(models.Document)
            .filter_by(container=None, path=path)
            .first()
            or models.Document(path=path)
        )
        if row.generation == self.generation:
            return

        print(path)

        try:
            (text, warnings, flags, size_disk) = EmailParser.parse(file)
        except Exception as e:
            self.exceptions += 1

        else:
            row.text = text
            row.warnings = warnings
            row.flags = flags
            row.size_text = len(text)
            row.size_disk = size_disk
            row.generation = self.generation
            self.session.add(row)
            self.processed += 1
            self.uncommitted += 1

            if self.uncommitted >= 100:
                print('COMMIT')
                # TODO commit
                self.uncommitted = 0
