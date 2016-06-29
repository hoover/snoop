import re
import subprocess
import codecs
import tempfile
import email, email.header, email.utils
from contextlib import contextmanager
from collections import defaultdict
from bs4 import BeautifulSoup
from pathlib import Path
from django.conf import settings
from . import models
from .utils import chunks


def decode_header(header):
    return str(email.header.make_header(email.header.decode_header(header)))

def text_from_html(html):
    soup = BeautifulSoup(html, 'lxml')
    for node in soup(["script", "style"]):
        node.extract()
    return re.sub(r'\s+', ' ', soup.get_text().strip())


def people(headers, header_names):
    values = []
    for name in header_names:
        for p in headers.get(name, []):
            values.append(p)
    return values

def extract_email_data(tree):
    headers = tree['headers']

    person_from = (people(headers, ['from']) + [''])[0]
    people_to = people(headers,
                       ['to', 'cc', 'bcc', 'resent-to', 'recent-cc',
                        'reply-to'])

    rv = {
        'subject': headers.get('subject', [''])[0],
        'from': person_from,
        'to': people_to,
        'attachments': tree.get('attachments', {}),
    }

    for header in ['message-id', 'in-reply-to',
                   'thread-index', 'references']:
        value = headers.get(header, [None])[0]
        if value:
            rv[header] = value

    message_date = headers.get('date', [None])[0]
    if message_date:
        try:
            date = email.utils.parsedate_to_datetime(message_date).isoformat()
        except:
            pass # TODO log a warning
        else:
            rv['date'] = date

    return rv

class CorruptedFile(Exception):
    pass

class PayloadError(Exception):
    pass

class EmailParser(object):

    def __init__(self, file):
        self.file = file
        self.warnings = []
        self.flags = set()
        self._parsed_message = None
        self._message() # TODO refactor so we don't parse the message here

    def warn(self, text):
        self.warnings.append(text)

    def flag(self, flag):
        self.flags.add(flag)

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
        part = dict(self.parts(self._message()))[number]
        self._get_part_content(part, number)
        tmp = tempfile.SpooledTemporaryFile()
        try:
            data = part.get_payload(decode=True)
        except:
            raise PayloadError
        tmp.write(data)
        tmp.seek(0)
        return tmp

    def parts_tree(self, message):
        headers = defaultdict(list)

        def _header(key, header):
            try:
                value = decode_header(header)

            except:
                value = str(header)
                key = '_broken_' + key

            headers[key].append(value)

        for key in message.keys():
            for header in message.get_all(key):
                _header(key.lower(), header)

        rv = {'headers': dict(headers)}

        if message.is_multipart():
            rv['parts'] = [self.parts_tree(p) for p in message.get_payload()]

        else:
            rv['length'] = len(message.get_payload())

        return rv

    def get_tree(self):
        return self.parts_tree(self._message())

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

    def get_attachments(self):
        message = self._message()
        rv = {}
        for number, part in self.parts(message):
            if not part.get_content_disposition(): continue
            filename = part.get_filename()
            if not filename: continue

            rv[number] = {
                'content_type': part.get_content_type().lower(),
                'filename': filename,
            }

        return rv

    def _message(self):
        if self._parsed_message is None:
            self._parsed_message = email.message_from_binary_file(self.file)
        return self._parsed_message

    def get_text(self):
        text_parts = []
        for _, part in self.parts(self._message()):
            text = self.get_part_text(part)
            if text:
                text_parts.append(text)
        return '\n'.join(text_parts)

class MissingEmlxPart(Exception):
    pass

class EmlxParser(EmailParser):

    def __init__(self, file, path):
        self.path = path
        super().__init__(file)

    def _get_part_content(self, part, number):
        if part.get('X-Apple-Content-Length'):
            ext = '.' + number + '.emlxpart'
            mail_id = re.sub(r'\.partial\.emlx$', ext, self.path.name)
            part_file = self.path.parent / mail_id

            try:
                with part_file.open() as f:
                    payload = f.read()
            except FileNotFoundError:
                raise MissingEmlxPart
            part.set_payload(payload)

    def _message(self):
        if self._parsed_message is None:
            try:
                (size, extra) = self.file.read(11).split(b'\n', 1)
            except:
                raise CorruptedFile
            raw = extra + self.file.read(int(size) - len(extra))
            self._parsed_message = email.message_from_bytes(raw)

        return self._parsed_message

def msgcache(func):
    if not (settings.MALDINI_CACHE and settings.MALDINI_MSG_CACHE):
        return func

    def wrapper(doc):
        d0 =  Path(settings.MALDINI_MSG_CACHE) /doc.sha1[:2]
        cached = d0 / (doc.sha1[2:] + '.eml')

        if not cached.is_file():
            with func(doc) as tmp:
                d0.mkdir(exist_ok=True)

                _tmp = tempfile.NamedTemporaryFile(dir=str(d0), delete=False)
                with _tmp as c:
                    for chunk in chunks(tmp):
                        c.write(chunk)

                Path(c.name).rename(cached)

        return cached.open('rb')

    return wrapper

@msgcache
@contextmanager
def open_msg(doc):
    if settings.MSGCONVERT_SCRIPT is None:
        raise RuntimeError("Path to 'msgconvert' is not configured")

    path = doc.absolute_path

    with tempfile.TemporaryDirectory(suffix='-snoop') as tmp:
        msg = Path(tmp) / path.name
        msg.symlink_to(path)

        subprocess.check_output(
            [settings.MSGCONVERT_SCRIPT, msg.name],
            cwd=tmp,
        )

        with msg.with_suffix('.eml').open('rb') as f:
            yield f

def is_email(doc):
    return doc.content_type in ['message/x-emlx',
                                'message/rfc822',
                                'application/vnd.ms-outlook']

def open_email(doc):
    if doc.content_type == 'message/x-emlx':
        with doc.open() as f:
            assert doc.container_id is None, "can't parse emlx in container"
            return EmlxParser(f, doc.absolute_path)

    if doc.content_type == 'message/rfc822':
        with doc.open() as f:
            return EmailParser(f)

    if doc.content_type == 'application/vnd.ms-outlook':
        with open_msg(doc) as f:
            return EmailParser(f)

    raise RuntimeError

def get_email_part(doc, part):
    return open_email(doc).open_part(part)

@models.cache(models.EmailCache, lambda doc: doc.id)
def raw_parse_email(doc):
    email = open_email(doc)
    return {
        'tree': email.get_tree(),
        'attachments': email.get_attachments(),
        'text': email.get_text(),
    }

def parse_email(doc):
    parsed = raw_parse_email(doc)
    data = extract_email_data(parsed['tree'])
    data.update({
        'text': parsed['text'],
        'tree': parsed['tree'],
        'attachments': parsed['attachments'],
    })
    return data
