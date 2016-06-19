from django.conf import settings
import email, email.header, email.utils
import re
from pprint import pformat
from pathlib import Path
from tempfile import TemporaryFile
import subprocess
import codecs
import hashlib
from .tikalib import tika_parse, extract_meta
from bs4 import BeautifulSoup
import dateutil.parser
from io import StringIO

FILE_TYPES = {
    'application/x-directory': 'folder',
    'application/vnd.oasis.opendocument.text': 'doc',
    'application/pdf': 'pdf',
    'application/msword': 'doc',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'doc',
    'application/vnd.ms-excel': 'xls',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xls',
    'text/plain': 'text',
    'text/html': 'html',
    'message/x-emlx': 'email',
    'message/rfc822': 'email'
}

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
        self.message = self._message()
        self.data = self.parse()

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

    def _get_part_content(self, part, number):
        pass

    def open_part(self, number):
        part = dict(self.parts(self.message))[number]
        self._get_part_content(part, number)
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

    def get_tree(self):
        return pformat(self.parts_tree(self.message))

    def get_data(self):
        return self.data

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
                disposition.lower())
            if not m: continue
            content_type = str(part.get('content-type', '')).split(';')[0].strip()
            yield number, {
                'content_type': content_type.lower(),
                'filename': m.group('filename'),
            }

    def _message(self):
        return email.message_from_binary_file(self.file)

    def parse(self):
        person_from = (list(self.people(self.message, ['from'])) + [''])[0]
        people_to = list(self.people(self.message, ['to', 'cc', 'resent-to', 'recent-cc', 'reply-to']))
        text_parts = []
        for _, part in self.parts(self.message):
            text = self.get_part_text(part)
            if text:
                text_parts.append(text)

        rv = {
            'subject': str(self.message.get('subject')),
            'from': person_from,
            'to': people_to,
            'date': dateutil.parser.parse(self.message.get('date')).isoformat(),
            'text': '\n'.join(text_parts),
            'attachments': dict(self.get_attachments(self.message)),
        }
        return rv

class EmlxParser(EmailParser):

    def __init__(self, file, path):
        self.path = path
        super().__init__(file)

    def _get_part_content(self, part, number):
        if part.get('X-Apple-Content-Length'):
            ext = '.' + number + '.emlxpart'
            mail_id = re.sub(r'\.partial\.emlx$', ext, self.path.name)
            part_file = self.path.parent / mail_id

            with part_file.open() as f:
                payload = f.read()
            part.set_payload(payload)

    def _message(self):
        (size, extra) = self.file.read(11).split(b'\n', 1)
        raw = extra + self.file.read(int(size) - len(extra))
        return email.message_from_bytes(raw)

def doc_path(doc):
    return Path(settings.MALDINI_ROOT) / doc.path

def is_email(doc):
    return doc.content_type in ['message/x-emlx', 'message/rfc822']

def open_email(doc):
    if doc.content_type == 'message/x-emlx':
        with open_document(doc) as f:
            return EmlxParser(f, doc_path(doc))

    if doc.content_type == 'message/rfc822':
        with open_document(doc) as f:
            return EmailParser(f)

    raise RuntimeError

def open_document(doc):
    if doc.content_type == 'application/x-directory':
        return StringIO()

    if doc.container is None:
        path = doc_path(doc)
        return path.open('rb')

    else:
        if is_email(doc.container):
            return open_email(doc.container).open_part(doc.path)

    raise RuntimeError

def _path_bits(doc):
    if doc.container:
        yield from _path_bits(doc.container)
    yield doc.path

def _calculate_hashes(opened_file):
    BUF_SIZE = 65536

    md5 = hashlib.md5()
    sha1 = hashlib.sha1()

    while True:
        data = opened_file.read(BUF_SIZE)
        if not data:
            break
        md5.update(data)
        sha1.update(data)

    fsize = opened_file.tell()

    return (md5.hexdigest(), sha1.hexdigest(), fsize)

def guess_filetype(doc):

    content_type = doc.content_type.split(';')[0]  # for: text/plain; charset=ISO-1234

    return FILE_TYPES.get(content_type)

def digest(doc):
    with open_document(doc) as f:

        if not doc.sha1:
            md5, sha1, fsize = _calculate_hashes(f)
            f.seek(0)
            if not doc.disk_size:
                doc.disk_size = fsize
            doc.sha1 = sha1
            doc.md5 = md5
            doc.save()

        data = {
            'title': '|'.join(_path_bits(doc)),
            'lang': None,
            'sha1': doc.sha1,
            'md5': doc.md5,
        }

        if doc.container_id is None:
            data['path'] = doc.path

            if is_email(doc):
                email = open_email(doc)
                data.update(email.get_data())
                data['parts'] = email.get_tree()

        filetype = guess_filetype(doc)
        data['type'] = filetype

        if filetype in settings.TIKA_FILE_TYPES and doc.disk_size <= settings.MAX_TIKA_FILE_SIZE:
            parsed = tika_parse(doc.sha1, f.read())
            data['text'] = (parsed.get('content') or '').strip()
            data.update(extract_meta(parsed['metadata']))

        return data
