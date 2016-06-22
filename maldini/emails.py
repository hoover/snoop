import email, email.header, email.utils
import re
from pprint import pformat
from tempfile import TemporaryFile
import codecs
import dateutil.parser
from bs4 import BeautifulSoup


def decode_header(header):
    return str(email.header.make_header(email.header.decode_header(header)))

def text_from_html(html):
    soup = BeautifulSoup(html, 'lxml')
    for node in soup(["script", "style"]):
        node.extract()
    return re.sub(r'\s+', ' ', soup.get_text().strip())

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
        part = dict(self.parts(self._message()))[number]
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
        return pformat(self.parts_tree(self._message()))

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

    def get_data(self):
        message = self._message()  # TODO use self.get_tree()
        person_from = (list(self.people(message, ['from'])) + [''])[0]
        people_to = list(self.people(message,
                                     ['to', 'cc', 'resent-to',
                                      'recent-cc', 'reply-to']))

        rv = {
            'subject': decode_header(message.get('subject') or ''),
            'from': decode_header(person_from),
            'to': [decode_header(h) for h in people_to],
            'attachments': dict(self.get_attachments(message)),
        }

        try:
            message_date = message.get('date')
            date = dateutil.parser.parse(message_date).isoformat()
        except:
            pass  # TODO: log a warning that the date is not parsable
        else:
            rv['date'] = date

        return rv

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
        try:
            (size, extra) = self.file.read(11).split(b'\n', 1)
        except:
            raise CorruptedFile
        raw = extra + self.file.read(int(size) - len(extra))
        return email.message_from_bytes(raw)
