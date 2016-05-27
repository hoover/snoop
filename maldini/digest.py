from django.conf import settings
import email, email.header, email.utils
import re
from pprint import pformat
from pathlib import Path
from tempfile import TemporaryFile
import subprocess
from bs4 import BeautifulSoup
from .models import Document, FolderMark

def pdftotext(input):
    return subprocess.check_output(['pdftotext', '-', '-'], stdin=input)

def text_from_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    for node in soup(["script", "style"]):
        node.extract()
    return re.sub(r'\s+', ' ', soup.get_text().strip())

def _decode_header(headervalue):
    return [
        value.decode(encoding) if encoding else value
        for (value, encoding) in email.header.decode_header(headervalue)
    ]

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
        (name, addr) = email.utils.parseaddr(header)
        return ' '.join(_decode_header(name) + [addr])

    def people(self, message, headers):
        for header in headers:
            for p in (self.decode_person(h) for h in message.get_all(header, [])):
                yield p

    def parts(self, message, number_bits=[]):
        if message.is_multipart():
            for i, part in enumerate(message.get_payload(), 1):
                for p in self.parts(part, number_bits + [str(i)]):
                    yield p
        else:
            yield '.'.join(number_bits), message

    def open_part(self, number):
        message = self._message()
        part = dict(self.parts(message))[number]
        tmp = TemporaryFile()
        tmp.write(part.get_payload(decode=True))
        tmp.seek(0)
        return tmp

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
        for number, part in self.parts(message):
            disposition = part.get('content-disposition')
            if not disposition: continue
            m = re.match(r'^(inline|attachment);\s+filename=(?P<filename>.*)$',
                disposition)
            if not m: continue
            content_type = part.get('content-type', '').split(';')[0].strip()
            yield number, {
                'content_type': content_type,
                'filename': m.group('filename'),
            }

    def _message(self):
        with self.file.open('rb') as f:
            (size, extra) = f.read(11).split(b'\n', 1)
            raw = extra + f.read(int(size) - len(extra))

        return email.message_from_bytes(raw)

    @classmethod
    def parse(cls, file, parts=False):
        self = cls(file)
        message = self._message()
        person_from = (list(self.people(message, ['from'])) + [''])[0]
        people_to = list(self.people(message, ['to', 'cc', 'resent-to', 'recent-cc', 'reply-to']))
        text_parts = []
        for _, part in self.parts(message):
            text = self.get_part_text(part)
            if text:
                text_parts.append(text)

        rv = {
            'subject': message.get('subject'),
            'from': person_from,
            'to': people_to,
            'date': message.get('date'),
            'text': '\n'.join(text_parts),
            'attachments': dict(self.get_attachments(message)),
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
        return str(file.relative_to(self.root))

    def handle(self, file=None):
        if file is None:
            file = self.root

        if file.is_dir():
            path = self._path(file)
            if FolderMark.objects.filter(path=path).count():
                print('SKIP', path)
                return
            for child in file.iterdir():
                self.handle(child)
            FolderMark.objects.create(path=path)
            print('MARK', path)

        else:
            self.handle_file(file)

    def handle_file(self, file):
        path = self._path(file)
        print('FILE', path)
        doc, _ = Document.objects.get_or_create(path=path, defaults={'disk_size': file.stat().st_size})
        doc.save()

        #if file.suffixes[-1:] == ['.emlx']:
        #    self.handle_emlx(file)

    def handle_emlx(self, file):
        path = unicode(file.relative_to(self.root))
        row = (
            self.session
            .query(Document)
            .filter_by(container=None, path=path)
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

def open_document(doc):
    if doc.container is None:
        file = Path(settings.MALDINI_ROOT) / doc.path
        return file.open('rb')

    if doc.container.path.endswith('.emlx'):
        file = Path(settings.MALDINI_ROOT) / doc.container.path
        email = EmailParser(file)
        return email.open_part(doc.path)

    raise RuntimeError

def digest(doc):
    data = {
        'title': doc.path,
        'path': doc.path,
        'disk_size': doc.disk_size,
    }

    if doc.container_id is None:
        file = Path(settings.MALDINI_ROOT) / doc.path
        if file.suffix == '.emlx':
            data['type'] = 'email'
            data.update(EmailParser.parse(file, parts=True))

    if doc.content_type == 'application/pdf':
        with open_document(doc) as f:
            data['text'] = pdftotext(f)

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
