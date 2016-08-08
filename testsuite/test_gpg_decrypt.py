import tempfile
import json
from pathlib import Path

from email.message import EmailMessage
from email.headerregistry import Address

import gnupg
import pytest

from maldini import pgp
from django.conf import settings

# http://www.saltycrane.com/blog/2011/10/python-gnupg-gpg-example/
# If it stalls:     ` $ sudo apt-get install rng-tools `

# To manually remove the passphrase from a key:
# http://www.cyberciti.biz/faq/linux-unix-gpg-change-passphrase-command/

@pytest.yield_fixture
def patch_gpg_to_temp_dir(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        gpg = gnupg.GPG(gnupghome=tmp, gpgbinary='gpg')
        monkeypatch.setattr(pgp, 'GPG', gpg)
        monkeypatch.setattr(settings, 'MALDINI_GPG_HOME', '/tmp')
        monkeypatch.setattr(settings, 'MALDINI_GPG_BINARY', 'gpg')
        yield

def test_decryption(patch_gpg_to_temp_dir):

    def create_profile(gpg, name, email, passphrase):
        input_data = gpg.gen_key_input(
            name_email=email,
            passphrase=passphrase)
        key = gpg.gen_key(input_data)
        fingerprint = str(key)
        public = gpg.export_keys(fingerprint)
        private = gpg.export_keys(fingerprint, True)
        return {
            'fingerprint': fingerprint,
            'passphrase': passphrase,
            'email': email,
            'name': name,
            'public': public,
            'private': private,
        }

    def create_email(gpg, profile_from, profile_to, path):
        msg = EmailMessage()
        msg['Subject'] = "[spam] Hey there sexy"
        msg['From'] = Address(profile_from['name'], profile_from['email'])
        msg['To'] = Address(profile_from['name'], profile_from['email'])
        clear_text = "Let's do something interesting"
        encrypted_data = gpg.encrypt(clear_text, [profile_to['email'],
                                                  profile_from['email']])
        encrypted_string = str(encrypted_data)
        msg.set_content(encrypted_string)

        with path.open('wb') as f:
            f.write(bytes(msg))

    def setup(gpg, path):
        A = {
            'name': 'Unsuspecting',
            'email': 'unsusp@ect.ing',
            'passphrase': 'correct horse battery staple',
        }

        B = {
            'name': 'Foxxy',
            'email': 'dub@io.us',
            'passphrase': '018y2hirfnalsyf03'
        }

        profileA = create_profile(gpg, **A)
        profileB = create_profile(gpg, **B)

        create_email(gpg, profileA, profileB, path / "1.eml")
        create_email(gpg, profileB, profileA, path / "2.eml")

        with (path / 'data.json').open('w') as f:
            json.dump({
                'profiles': [profileA, profileB]
            }, f, indent=4, sort_keys=True)


    with tempfile.TemporaryDirectory(prefix="test_snoop_gpg_home") as pathstr:
        path = Path(pathstr)
        gpg = pgp._get_gpg()
        setup(gpg, path)
        with (path / "data.json").open() as f:
            data = json.load(f)

        p = data['profiles'][0]
        keys = p['public'] + p['private']
        passphrase = p['passphrase']

        gpg.import_keys(keys)

        for i in range(1, 3):
            eml_path = path / ("%s.eml" % i)
            with eml_path.open() as f:
                block = f.read()
                result = pgp.decrypt_pgp_block(block, passphrase)
                assert result
