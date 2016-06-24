from pathlib import Path
from maldini import emails, digest

PATH_MSG_DISEARA = Path(r"msg-5-outlook/DISEARĂ-Te-așteptăm-la-"
                        "discuția-despre-finanțarea-culturii.msg")

def test_subject():
    email = emails.open_msg(digest.doc_path(PATH_MSG_DISEARA))
    data = email.get_data()

    assert data['subject'] == "DISEARĂ: Te așteptăm la " \
                              "discuția despre finanțarea culturii"

def test_text():
    email = emails.open_msg(digest.doc_path(PATH_MSG_DISEARA))

    assert "Te așteptăm diseară de la 19:00 la Colivia" in email.get_text()
    assert "Întâlnirile Culturale CALEIDO: Despre finanțarea culturii" in email.get_text()

def test_people():
    email = emails.open_msg(digest.doc_path(PATH_MSG_DISEARA))
    data = email.get_data()

    assert "cosmin@caleido.ro" in data['from']
    assert len(data['to']) == 1
    assert "cosmin@caleido.ro" == data['to'][0]


def test_tree_without_attachments():
    email = emails.open_msg(digest.doc_path(PATH_MSG_DISEARA))
    tree = email.get_tree()

    headers = {'Subject', 'To', 'From', 'Date', 'Content-Type'}
    assert headers.issubset(set(tree['headers'].keys()))

    assert set(tree.keys()) == {'headers', 'parts'}
    assert len(tree['parts']) == 2

