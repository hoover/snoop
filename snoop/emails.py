import re
import subprocess
import codecs
import tempfile
import email, email.header, email.utils
from contextlib import contextmanager
from collections import defaultdict
from io import BytesIO
from pathlib import Path
from django.conf import settings
from . import models
from . import exceptions
from .utils import chunks
from .html import text_from_html
from .content_types import guess_content_type
from . import pgp


def decode_header(header):
    return str(email.header.make_header(email.header.decode_header(header)))

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
            pass
        else:
            rv['date'] = date

    return rv

class CorruptedFile(exceptions.BrokenDocument):
    flag = 'emails_corrupted_file'

class PayloadError(exceptions.BrokenDocument):
    flag = 'emails_payload_error'

class EmailParser(object):

    def __init__(self, file):
        self.file = file
        self.pgp = False
        self._parsed_message = None
        self._message() # TODO refactor so we don't parse the message here

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

        if self.pgp and \
                pgp.is_enabled() and \
                pgp.contains_pgp_block(data):
            data = pgp.decrypt_pgp_block(data)

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
        def get_payload(encrypted=False):
            try:
                payload_bytes = part.get_payload(decode=True)
                if encrypted:
                    payload_bytes = pgp.decrypt_pgp_block(payload_bytes)
            except Exception as e:
                return "(Error: {t.__name__})".format(t=type(e))

            charset = part.get_content_charset() or 'latin-1'
            try:
                codecs.lookup(charset)
            except LookupError:
                charset = 'latin-1'
            return payload_bytes.decode(charset, errors='replace')

        if content_type == 'text/plain':
            if self.pgp and pgp.is_enabled():
                if 'content-disposition' not in part:
                    return get_payload(True)
            else:
                return get_payload()

        if content_type == 'text/html':
            return text_from_html(get_payload())

    def get_attachments(self):
        message = self._message()
        rv = {}
        for number, part in self.parts(message):
            if not part.get_content_disposition(): continue
            filename = part.get_filename()
            if not filename: continue
            filename = decode_header(filename)
            content_type = part.get_content_type().lower()
            if content_type == "application/octet-stream":
                content_type = guess_content_type(filename)
            if content_type == 'text/plain' and self.pgp and pgp.is_enabled():
                content_type = guess_content_type(filename)

            rv[number] = {
                'content_type': content_type,
                'filename': filename,
                'size': len(part.get_payload()),
            }

        return rv

    def _message(self):
        if self._parsed_message is None:
            data = self.file.read()
            if pgp.contains_pgp_block(data):
                self.pgp = True
            self._parsed_message = email.message_from_bytes(data)
        return self._parsed_message

    def get_text(self):
        text_parts = []
        for _, part in self.parts(self._message()):
            text = self.get_part_text(part)
            if text:
                text_parts.append(text)
        return '\n'.join(text_parts)

class MissingEmlxPart(exceptions.BrokenDocument):
    flag = 'emails_missing_emlx_part'

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
            if pgp.contains_pgp_block(raw):
                self.pgp = True
            self._parsed_message = email.message_from_bytes(raw)

        return self._parsed_message

def msgcache(func):
    if not (settings.SNOOP_CACHE and settings.SNOOP_MSG_CACHE):
        return func

    def wrapper(doc):
        d0 =  Path(settings.SNOOP_MSG_CACHE) /doc.sha1[:2]
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
    if settings.SNOOP_MSGCONVERT_SCRIPT is None:
        raise RuntimeError("Path to 'msgconvert' is not configured")

    if doc.flags.get('msgconvert_fail'):
        yield BytesIO()
        return

    with tempfile.TemporaryDirectory(suffix='-snoop') as tmp, \
            doc.open(filesystem=True) as file:
        path = file.path
        msg = Path(tmp) / path.name
        msg.symlink_to(path)

        try:
            subprocess.check_output(
                [settings.SNOOP_MSGCONVERT_SCRIPT, msg.name],
                cwd=tmp,
            )
        except:
            if settings.SNOOP_FLAG_MSGCONVERT_FAIL:
                doc.flags['msgconvert_fail'] = True
                doc.save()
                yield BytesIO()
                return

            raise

        with msg.with_suffix('.eml').open('rb') as f:
            yield f

def is_email(doc):
    return doc.content_type in ['message/x-emlx',
                                'message/rfc822',
                                'application/vnd.ms-outlook']

def open_email(doc):
    email = None

    if doc.content_type == 'message/x-emlx':
        with doc.open() as f:
            assert doc.container_id is None, "can't parse emlx in container"
            email = EmlxParser(f, doc.absolute_path)

    if doc.content_type == 'message/rfc822':
        with doc.open() as f:
            email = EmailParser(f)

    if doc.content_type == 'application/vnd.ms-outlook':
        with open_msg(doc) as f:
            email = EmailParser(f)

    if email is None:
        raise RuntimeError

    if email.pgp:
        if 'pgp' not in doc.flags:
            doc.flags['pgp'] = True
            doc.save()

    return email

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
