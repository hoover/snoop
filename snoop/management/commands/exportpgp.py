from django.core.management.base import BaseCommand
from pathlib import Path
import base64
from ... import models
from ... import emails
from ... import pgp
from ... import utils
from ...content_types import guess_content_type

class Command(BaseCommand):
    help = "Export digested pgp .eml files to a zip archive"

    def add_arguments(self, parser):
        parser.add_argument('destination',
            help='path to the folder where the files will be dumped')
        parser.add_argument('--where', default="(flags->>'pgp')::bool",
            help='SQL "WHERE" clause on the snoop_document table')


    def handle(self, destination, where, **options):
        query = utils.build_raw_query('snoop_document', where)
        root = Path(destination)
        done = 0
        for doc in models.Document.objects.raw(query):
            if emails.is_email(doc):
                email = emails.open_email(doc)
                if not email.pgp:
                    print("id:", doc.id, "is not a pgp-encrypted email")
                    continue
                try:
                    output = decrypt_email_file(email)
                    dump_eml(root, doc.md5, output)
                except Exception as e:
                    print("id:", doc.id, "failed: " + type(e).__name__)
                else:
                    print("id:", doc.id, "is done")
                    done += 1
            else:
                print("id:", doc.id, "is not an email file")
        print(done, "documents dumped.")


def decrypt_email_file(email):
    message = email._message()
    for part in message.walk():
        if part.is_multipart():
            continue
        content_type = part.get_content_type()
        filename = part.get_filename()
        if filename:
            if content_type == 'text/plain' or \
                    content_type == "application/octet-stream":
                content_type = guess_content_type(filename)
        part.set_type(content_type)

        if filename == "message.html.pgp":
            del part['Content-Disposition']
            part.add_header('Content-Disposition',
                            'attachment',
                            filename='pgp.message.html')
            part.replace_header('Content-Type', 'text/html')

        data = part.get_payload(decode=True)
        if not data:
            continue
        if pgp.contains_pgp_block(data):
            data = pgp.decrypt_pgp_block(data)
            b64 = base64.encodebytes(data)
            part.set_payload(b64)
            del part['Content-Transfer-Encoding']
            part['Content-Transfer-Encoding'] = 'base64'
    return message.as_bytes()


def dump_eml(root_path, md5, data):
    folder = root_path / md5[0:2] / md5[2:4]
    folder.mkdir(parents=True, exist_ok=True)
    file = folder / (md5 + '.eml')
    with file.open('wb') as f:
        f.write(data)
