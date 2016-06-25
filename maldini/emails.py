import re
import subprocess
import codecs
import tempfile
import email, email.header, email.utils
from tempfile import SpooledTemporaryFile
from contextlib import contextmanager
from bs4 import BeautifulSoup
from pathlib import Path
from django.conf import settings


def decode_header(header):
    return str(email.header.make_header(email.header.decode_header(header)))

def text_from_html(html):
    soup = BeautifulSoup(html, 'lxml')
    for node in soup(["script", "style"]):
        node.extract()
    return re.sub(r'\s+', ' ', soup.get_text().strip())

def people(message, headers):
    def _decode_person(header):
        (name, addr) = email.utils.parseaddr(str(header))
        return ' '.join([str(email.header.Header(name)) + addr])

    for header in headers:
        for p in (_decode_person(h) for h in message.get_all(header, [])):
            yield p

def extract_email_data(tree):
    message = email.message.Message()
    for name, value in tree['headers'].items():
        message[name] = value

    person_from = (list(people(message, ['from'])) + [''])[0]
    people_to = list(people(message,
        ['to', 'cc', 'resent-to', 'recent-cc', 'reply-to']))

    rv = {
        'subject': decode_header(message.get('subject') or ''),
        'from': decode_header(person_from),
        'to': [decode_header(h) for h in people_to],
        'attachments': tree.get('attachments', {}),
    }

    for header in ['message-id', 'in-reply-to',
                   'thread-index', 'references']:
        value = message.get(header)
        if value:
            rv[header] = decode_header(value)

    message_date = message.get('date')
    date = email.utils.parsedate_to_datetime(message_date).isoformat()
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
        tmp = SpooledTemporaryFile()
        try:
            data = part.get_payload(decode=True)
        except:
            raise PayloadError
        tmp.write(data)
        tmp.seek(0)
        return tmp

    def parts_tree(self, message):
        if message.is_multipart():
            children = [self.parts_tree(p) for p in message.get_payload()]
            rv = {'headers': dict(message)}
            if children:
                rv['parts'] = children
            return rv
        else:
            return {
                'headers': dict(message),
                'length': len(message.get_payload()),
            }

    def get_tree(self):
        tree = self.parts_tree(self._message())
        attachments = dict(self.get_attachments(self._message()))
        if attachments:
            tree['attachments'] = attachments
        return tree

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
            if not part.get_content_disposition(): continue
            filename = part.get_filename()
            if not filename: continue

            yield number, {
                'content_type': part.get_content_type().lower(),
                'filename': filename,
            }

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

@contextmanager
def open_msg(path):
    if settings.MSGCONVERT_SCRIPT is None:
        raise RuntimeError("Path to 'msgconvert' is not configured")

    with tempfile.TemporaryDirectory(suffix='-snoop') as tmp:
        msg = Path(tmp) / path.name
        msg.symlink_to(path)

        subprocess.check_call(
            [settings.MSGCONVERT_SCRIPT, msg.name],
            cwd=tmp,
            stderr=subprocess.DEVNULL, # msgconvert produces some garbage
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
        with open_msg(doc.absolute_path) as f:
            return EmailParser(f)

    raise RuntimeError

def get_email_part(doc, part):
    return open_email(doc).open_part(part)

def raw_parse_email(doc):
    email = open_email(doc)
    tree = email.get_tree()
    text = email.get_text()
    return (tree, text)

def parse_email(doc):
    (tree, text) = raw_parse_email(doc)
    data = extract_email_data(tree)
    data['text'] = text
    data['tree'] = tree
    return data
