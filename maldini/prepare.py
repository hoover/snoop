from django.conf import settings
import email, email.header, email.utils
import re
from pprint import pformat
from pathlib import Path
from bs4 import BeautifulSoup
from .models import Document, FolderMark

def text_from_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    for node in soup(["script", "style"]):
        node.extract()
    return re.sub(r'\s+', ' ', soup.get_text().strip())

class EmailParser(object):

    def __init__(self, file):
        self.file = file
        self.warnings = []
        self.flags = set()

    def warn(self, text):
        self.warnings.append(text)

    def flag(self, flag):
        self.flags.add(flag)

    def decode_person(self, header):
        (name_bytes, addr) = email.utils.parseaddr(header)
        name_parts = [
            bytes.decode(encoding or 'latin-1')
            for (bytes, encoding) in email.header.decode_header(name_bytes)
        ]
        return ' '.join(name_parts + [addr.decode('latin-1')])

    def people(self, message, headers):
        for header in headers:
            for p in (self.decode_person(h) for h in message.get_all(header, [])):
                yield p

    def parts(self, message):
        if message.is_multipart():
            for part in message.get_payload():
                for p in self.parts(part):
                    yield p
        else:
            yield message

    def parts_tree(self, message):
        if message.is_multipart():
            children = [self.parts_tree(p) for p in message.get_payload()]
            return [dict(message), children]
        else:
            return [dict(message), len(message.get_payload())]

    def get_part_text(self, part):
        charset = part.get_content_charset()
        content_type = part.get_content_type()
        payload = lambda: part.get_payload(decode=True).decode(charset or 'latin-1')
        if content_type == 'text/plain':
            return payload()
        if content_type == 'text/html':
            return text_from_html(payload())
        self.warn("Unknown part content type: %r" % content_type)
        self.flag('unknown_attachment')

    def get_attachments(self, message):
        for part in self.parts(message):
            disposition = part.get('content-disposition')
            if not disposition: continue
            m = re.match(r'^attachment;\s+filename=(.*)$', disposition)
            if not m: continue
            yield m.group(1)

    @classmethod
    def parse(cls, file, parts=False):
        self = cls(file)

        with self.file.open('rb') as f:
            (size, extra) = f.read(11).split('\n', 1)
            raw = extra + f.read(int(size) - len(extra))

        message = email.message_from_string(raw)
        [person_from] = self.people(message, ['from'])
        people_to = list(self.people(message, ['to', 'cc', 'resent-to', 'recent-cc', 'reply-to']))
        text_parts = []
        for part in self.parts(message):
            text = self.get_part_text(part)
            if text:
                text_parts.append(text)

        rv = {
            'subject': message.get('subject'),
            'from': person_from,
            'to': people_to,
            'date': message.get('date'),
            'text': '\n'.join(text_parts),
            'attachments': list(self.get_attachments(message)),
        }
        if parts:
            rv['parts'] = pformat(self.parts_tree(message))
        return rv

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
        return str(file.relative_to(self.root)).decode('utf-8')

    def handle(self, file=None):
        if file is None:
            file = self.root

        if file.is_dir():
            path = self._path(file)
            if FolderMark.objects.filter(path=path).count():
                print 'SKIP', path
                return
            for child in file.iterdir():
                self.handle(child)
            FolderMark.objects.create(path=path)
            print 'MARK', path

        else:
            self.handle_file(file)

    def handle_file(self, file):
        path = self._path(file)
        print 'FILE', path
        doc, _ = Document.objects.get_or_create(path=path, defaults={'disk_size': file.stat().st_size})
        doc.save()

        #if file.suffixes[-1:] == ['.emlx']:
        #    self.handle_emlx(file)

    def handle_emlx(self, file):
        path = unicode(file.relative_to(self.root))
        row = (
            self.session
            .query(Document)
            .filter_by(path=path)
            .first()
            or Document(path=path)
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

def extract(doc):
    file = Path(settings.MALDINI_ROOT) / doc.path.encode('utf-8')
    data = {
        'title': doc.path,
        'path': doc.path,
        'suffix': file.suffix.strip('.'),
        'disk_size': doc.disk_size,
    }

    if file.suffix == '.emlx':
        data['type'] = 'email'
        data.update(EmailParser.parse(file, parts=True))

    return data

def main():
    import sys
    Base.metadata.create_all(engine)
    generation = int(sys.argv[1])
    root = sys.argv[2]
    prefix = sys.argv[3] if len(sys.argv) > 3 else None
    (processed, exceptions) = Walker.walk(generation, root, prefix)
    print('processed = %d, exceptions = %d' % (processed, exceptions))

if __name__ == '__main__':
    main()
