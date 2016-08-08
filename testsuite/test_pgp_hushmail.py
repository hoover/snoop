import pytest
import gnupg
import tempfile
from django.conf import settings
from maldini import emails, models, pgp

PATH_HUSH_MAIL = 'eml-9-pgp/encrypted-hushmail-knockoff.eml'
HEIN_PRIVATE_KEY = 'eml-9-pgp/keys/hein-priv.gpg'
HEIN_PUBLIC_KEY = 'eml-9-pgp/keys/hein-pub.gpg'

@pytest.yield_fixture(autouse=True)
def patch_gpg_to_temp_dir(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        gpg = gnupg.GPG(gnupghome=tmp, gpgbinary='gpg')
        for path in [HEIN_PRIVATE_KEY, HEIN_PUBLIC_KEY]:
            with open(settings.MALDINI_ROOT + "/" + path, 'rb') as f:
                gpg.import_keys(f.read())
        monkeypatch.setattr(pgp, 'GPG', gpg)
        monkeypatch.setattr(settings, 'MALDINI_GPG_HOME', '/tmp')
        monkeypatch.setattr(settings, 'MALDINI_GPG_BINARY', 'gpg')
        yield

def parse_email(path):
    doc = models.Document(path=path, content_type='message/rfc822')
    return emails.parse_email(doc)

def open_email(path):
    doc = models.Document(path=path, content_type='message/rfc822')
    return emails.open_email(doc)

def test_header_data():
    data = parse_email(PATH_HUSH_MAIL)
    assert data['subject'] == "Fwd: test email"
    assert data['date'] == '2016-08-10T15:00:00'

def test_attachments():
    data = parse_email(PATH_HUSH_MAIL)
    attach = data['attachments']
    assert len(attach) == 6

    email = open_email(PATH_HUSH_MAIL)
    assert 'encrypted' in email.flags

    with email.open_part('3') as f:
        text = f.read().decode()
        assert "This is GPG v1 speaking!" in text
        assert "Sent from my Android piece of !@#%." in text