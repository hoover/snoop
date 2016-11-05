from snoop import models, emails

PATH_MSG_DISEARA = ("msg-5-outlook/DISEARĂ-Te-așteptăm-la-"
                    "discuția-despre-finanțarea-culturii.msg")

def parse_email(path, collection):
    doc = models.Document(
        path=path,
        content_type='application/vnd.ms-outlook',
        collection=collection,
    )
    return emails.parse_email(doc)

def test_content(document_collection):
    data = parse_email(PATH_MSG_DISEARA, document_collection)
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

