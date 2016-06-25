from pathlib import Path
from django.conf import settings
from maldini import emails

PATH_MSG_DISEARA = ("msg-5-outlook/DISEARĂ-Te-așteptăm-la-"
                    "discuția-despre-finanțarea-culturii.msg")

def open_msg(path):
    return emails.open_msg(Path(settings.MALDINI_ROOT) / path)

def test_subject():
    email = open_msg(PATH_MSG_DISEARA)
    data = email.get_data()

    assert data['subject'] == "DISEARĂ: Te așteptăm la " \
                              "discuția despre finanțarea culturii"

def test_text():
    email = open_msg(PATH_MSG_DISEARA)

    assert "Te așteptăm diseară de la 19:00 la Colivia" in email.get_text()
    assert "Întâlnirile Culturale CALEIDO: Despre finanțarea culturii" in email.get_text()

def test_people():
    email = open_msg(PATH_MSG_DISEARA)
    data = email.get_data()

    assert "cosmin@caleido.ro" in data['from']
    assert len(data['to']) == 1
    assert "cosmin@caleido.ro" == data['to'][0]


def test_tree_without_attachments():
    email = open_msg(PATH_MSG_DISEARA)
    tree = email.get_tree()

    headers = {'Subject', 'To', 'From', 'Date', 'Content-Type'}
    assert headers.issubset(set(tree['headers'].keys()))

    assert set(tree.keys()) == {'headers', 'parts'}
    assert len(tree['parts']) == 2

