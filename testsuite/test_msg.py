from pathlib import Path
from django.conf import settings
from maldini import emails

PATH_MSG_DISEARA = ("msg-5-outlook/DISEARĂ-Te-așteptăm-la-"
                    "discuția-despre-finanțarea-culturii.msg")

def test_content():
    email = emails.open_msg(Path(settings.MALDINI_ROOT) / PATH_MSG_DISEARA)
    data = email.get_data()
    text = email.get_text()
    tree = email.get_tree()

    assert data['subject'] == "DISEARĂ: Te așteptăm la " \
                              "discuția despre finanțarea culturii"

    assert "Te așteptăm diseară de la 19:00 la Colivia" in text
    assert "Întâlnirile Culturale CALEIDO: Despre finanțarea culturii" in text

    assert "cosmin@caleido.ro" in data['from']
    assert len(data['to']) == 1
    assert "cosmin@caleido.ro" == data['to'][0]

    headers = {'Subject', 'To', 'From', 'Date', 'Content-Type'}
    assert headers.issubset(set(tree['headers'].keys()))

    assert set(tree.keys()) == {'headers', 'parts'}
    assert len(tree['parts']) == 2

