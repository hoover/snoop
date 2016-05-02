import email, email.header, email.utils
from pathlib import Path
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base

MAIL_HEADERS = ['From', 'To', 'Date']

engine = sa.create_engine('postgresql:///maldini')
Base = declarative_base()

class Document(Base):
    __tablename__ = 'document'
    id = sa.Column(sa.Text, primary_key=True)
    path = sa.Column(sa.Text)

class EmailParser(object):

    def __init__(self, file):
        self.file = file

    def decode_person(self, header):
        (name_bytes, addr) = email.utils.parseaddr(header)
        name_parts = [
            bytes.decode(encoding or 'latin-1')
            for (bytes, encoding) in email.header.decode_header(name_bytes)
        ]
        return ' '.join(name_parts + [addr.decode('latin-1')])

    def people(self, message):
        for header in ['from', 'to', 'cc', 'resent-to', 'recent-cc', 'reply-to']:
            for p in (self.decode_person(h) for h in message.get_all(header, [])):
                yield p

    def parts(self, message):
        if message.is_multipart():
            for part in message.get_payload():
                for p in self.parts(part):
                    yield p
        else:
            yield message

    def parse(self):
        with self.file.open('rb') as f:
            (size, extra) = f.read(11).split('\n', 1)
            raw = extra + f.read(int(size) - len(extra))

        message = email.message_from_string(raw)
        for p in self.people(message):
            print(p)

        for part in self.parts(message):
            print(part.get_content_type())

def process(file):
    if file.is_dir():
        for child in file.iterdir():
            process(child)
    else:
        if file.suffixes[-1:] == ['.emlx']:
            print(file)
            EmailParser(file).parse()

def main():
    import sys
    Base.metadata.create_all(engine)
    process(Path(sys.argv[1]))

if __name__ == '__main__':
    main()
