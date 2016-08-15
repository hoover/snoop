from snoop import models, emails

PATH_MSG_DISEARA = ("msg-5-outlook/DISEARĂ-Te-așteptăm-la-"
                    "discuția-despre-finanțarea-culturii.msg")

def parse_email(path):
    doc = models.Document(path=path, content_type='application/vnd.ms-outlook')
    return emails.parse_email(doc)

def test_content():
    data = parse_email(PATH_MSG_DISEARA)
    tree = data['tree']
    text = data['text']

    assert data['subject'] == "DISEARĂ: Te așteptăm la " \
                              "discuția despre finanțarea culturii"

    assert "Te așteptăm diseară de la 19:00 la Colivia" in text
    assert "Întâlnirile Culturale CALEIDO: Despre finanțarea culturii" in text

    assert "cosmin@caleido.ro" in data['from']
    assert len(data['to']) == 1
    assert "cosmin@caleido.ro" == data['to'][0]

    headers = {'subject', 'to', 'from', 'date', 'content-type'}
    assert headers.issubset(set(tree['headers'].keys()))

    assert set(tree.keys()) == {'headers', 'parts'}
    assert len(tree['parts']) == 2

