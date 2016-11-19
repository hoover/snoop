import tempfile
import gnupg
import pytest

from django.conf import settings
from snoop import emails, models, pgp

pytestmark = pytest.mark.skipif(not settings.SNOOP_GPG_BINARY,
    reason="SNOOP_GPG_BINARY not set")

PATH_HUSH_MAIL = 'eml-9-pgp/encrypted-hushmail-knockoff.eml'
HEIN_PRIVATE_KEY = 'eml-9-pgp/keys/hein-priv.gpg'
HEIN_PUBLIC_KEY = 'eml-9-pgp/keys/hein-pub.gpg'

@pytest.yield_fixture(autouse=True)
def patch_gpg_to_temp_dir(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        gpg = gnupg.GPG(gnupghome=tmp, gpgbinary='gpg')
        for path in [HEIN_PRIVATE_KEY, HEIN_PUBLIC_KEY]:
            with open(settings.SNOOP_ROOT + "/" + path, 'rb') as f:
                gpg.import_keys(f.read())
        monkeypatch.setattr(pgp, 'GPG', gpg)
        monkeypatch.setattr(settings, 'SNOOP_GPG_HOME', '/tmp')
        yield

def create_email_doc(path, collection):
    doc = models.Document(
        path=path,
        content_type='message/rfc822',
        collection=collection,
    )
    doc.save = lambda *a, **k: None
    return doc

def parse_email(path, document_collection):
    return emails.parse_email(create_email_doc(path, document_collection))

def open_email(path, document_collection):
    return emails.open_email(create_email_doc(path, document_collection))

def test_doc_flags(document_collection):
    doc = create_email_doc(PATH_HUSH_MAIL, document_collection)
    emails.parse_email(doc)
    assert doc.flags.get('pgp')

def test_header_data(document_collection):
    data = parse_email(PATH_HUSH_MAIL, document_collection)
    assert data['subject'] == "Fwd: test email"
    assert data['date'] == '2016-08-10T15:00:00'

def test_attachments(document_collection):
    data = parse_email(PATH_HUSH_MAIL, document_collection)
    attach = data['attachments']
    assert len(attach) == 6

    email = open_email(PATH_HUSH_MAIL, document_collection)
    assert email.pgp

    with email.open_part('3') as f:
        text = f.read().decode()
        assert "This is GPG v1 speaking!" in text
        assert "Sent from my Android piece of !@#%." in text
