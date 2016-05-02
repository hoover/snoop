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

def decode_person(header):
    (name_bytes, addr) = email.utils.parseaddr(header)
    name_parts = [
        bytes.decode(encoding or 'latin-1')
        for (bytes, encoding) in email.header.decode_header(name_bytes)
    ]
    return ' '.join(name_parts + [addr.decode('latin-1')])

def people(message):
    for header in ['from', 'to', 'cc', 'resent-to', 'recent-cc', 'reply-to']:
        for p in (decode_person(h) for h in message.get_all(header, [])):
            yield p

def read_mail(file):
    with file.open('rb') as f:
        size = int(f.read(11))
        raw = f.read(size)

    message = email.message_from_string(raw)
    for p in people(message):
        print(p)

def process(folder):
    read_mail(folder)

def main():
    import sys
    Base.metadata.create_all(engine)
    process(Path(sys.argv[1]))

if __name__ == '__main__':
    main()
