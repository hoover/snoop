import email, email.header, email.utils
import re
from pprint import pformat
from tempfile import TemporaryFile
import codecs
import dateutil.parser
from bs4 import BeautifulSoup

def text_from_html(html):
    soup = BeautifulSoup(html, 'lxml')
    for node in soup(["script", "style"]):
        node.extract()
    return re.sub(r'\s+', ' ', soup.get_text().strip())

class PayloadError(Exception):
    pass

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
            'text': '\n'.join(text_parts),
            'attachments': dict(self.get_attachments(self.message)),
        }

        try:
            message_date = self.message.get('date')
            date = dateutil.parser.parse(message_date).isoformat()
        except:
            pass # we can't use the date value, so ignore it
        else:
            rv['date'] = date

        return rv

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
        (size, extra) = self.file.read(11).split(b'\n', 1)
        raw = extra + self.file.read(int(size) - len(extra))
        return email.message_from_bytes(raw)
