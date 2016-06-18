from django.conf import settings
import email, email.header, email.utils
import re
from pprint import pformat
from pathlib import Path
from tempfile import TemporaryFile
import subprocess
import codecs
from bs4 import BeautifulSoup
from .models import Document

def pdftotext(input):
    return subprocess.check_output(['pdftotext', '-', '-'], stdin=input)

def text_from_html(html):
    soup = BeautifulSoup(html, 'lxml')
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
        (name, addr) = email.utils.parseaddr(str(header))
        return ' '.join([str(email.header.Header(name)) + addr])

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

        if part.get('X-Apple-Content-Length'):
            ext = '.' + number + '.emlxpart'
            mail_id = re.sub(r'\.partial\.emlx$', ext, self.file.name)
            part_file = self.file.parent / mail_id

            with part_file.open() as f:
                payload = f.read()
            part.set_payload(payload)

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
        content_type = part.get_content_type()
        def get_payload():
            try:
                payload_bytes = part.get_payload(decode=True)
            except:
                return '(error)'

            charset = part.get_content_charset() or 'latin-1'
            try:
                codecs.lookup(charset)
            except LookupError:
                charset = 'latin-1'
            return payload_bytes.decode(charset, errors='replace')

        if content_type == 'text/plain':
            return get_payload()

        if content_type == 'text/html':
            return text_from_html(get_payload())

        self.warn("Unknown part content type: %r" % content_type)
        self.flag('unknown_attachment')

    def get_attachments(self, message):
        for number, part in self.parts(message):
            disposition = str(part.get('content-disposition'))
            if not disposition: continue
            m = re.match(r'^(inline|attachment);\s+filename=(?P<filename>.*)$',
                disposition)
            if not m: continue
            content_type = str(part.get('content-type', '')).split(';')[0].strip()
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
            'subject': str(message.get('subject')),
            'from': person_from,
            'to': people_to,
            'date': str(message.get('date')),
            'text': '\n'.join(text_parts),
            'attachments': dict(self.get_attachments(message)),
        }
        if parts:
            rv['parts'] = pformat(self.parts_tree(message))
        return rv

def open_document(doc):
    if doc.container is None:
        file = Path(settings.MALDINI_ROOT) / doc.path
        return file.open('rb')

    if doc.container.path.endswith('.emlx'):
        file = Path(settings.MALDINI_ROOT) / doc.container.path
        email = EmailParser(file)
        return email.open_part(doc.path)

    raise RuntimeError

def files_in(parent_path):
    child_documents = Document.objects.filter(
        container=None,
        path__iregex=r'^' + re.escape(parent_path) + r'[^/]+$',
    )
    return [{
        'id': child.id,
        'filename': child.path[len(parent_path):]
    } for child in child_documents]

def _path_bits(doc):
    if doc.container:
        yield from _path_bits(doc.container)
    yield doc.path

def digest(doc):
    data = {
        'title': '|'.join(_path_bits(doc)),
    }

    if doc.container_id is None:
        data['path'] = doc.path

        file = Path(settings.MALDINI_ROOT) / doc.path
        if file.suffix == '.emlx':
            data['type'] = 'email'
            data.update(EmailParser.parse(file, parts=True))

        if doc.content_type == 'application/x-directory':
            data['type'] = 'folder'

    if doc.content_type == 'application/pdf':
        data['type'] = 'pdf'
        #with open_document(doc) as f:
            #pass

    return data
