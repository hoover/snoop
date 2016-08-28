import re
import gnupg
from django.conf import settings
from . import models

GPG = None

def is_enabled():
    return settings.SNOOP_GPG_HOME and settings.SNOOP_GPG_BINARY

def _get_gpg():
    global GPG
    if is_enabled():
        if not GPG:
            GPG = gnupg.GPG(gnupghome=settings.SNOOP_GPG_HOME,
                            gpgbinary=settings.SNOOP_GPG_BINARY)
        return GPG
    else:
        raise RuntimeError("MALDINI_GPG_BINARY or MALDINI_GPG_HOME not set")

class DecryptionError(models.BrokenDocument):
    flag = 'pgp_decryption_failed'

def extract_pgp_block(content):
    if isinstance(content, bytes):
        content = content.decode('ascii')
    m = re.search(
        r'-----BEGIN PGP MESSAGE-----[^-]+-----END PGP MESSAGE-----',
        content, re.DOTALL)
    if m:
        return m.group(0)
    else:
        return None

def contains_pgp_block(content):
    if isinstance(content, bytes):
        try:
            content = content.decode('ascii')
        except ValueError:
            return False
    m = re.search(r'-----BEGIN PGP MESSAGE-----', content)
    return bool(m)

def decrypt_pgp_block(content, passphrase=None):
    text_block = extract_pgp_block(content)
    if not text_block:
        return content

    gpg = _get_gpg()

    if passphrase:
        decrypt = gpg.decrypt(text_block, passphrase=passphrase)
    else:
        decrypt = gpg.decrypt(text_block)

    if decrypt.ok:
        return decrypt.data

    raise DecryptionError(decrypt.status)


