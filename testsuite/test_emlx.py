from maldini import digest, models, emails

PATH_EMLX_LEGE = "lists.mbox/F2D0D67E-7B19-4C30-B2E9-" \
                 "B58FE4789D51/Data/1/Messages/1498.partial.emlx"

def get_emlx_for_path(path):
    doc = models.Document(path=path)
    with digest.open_document(doc) as f:
        email = emails.EmlxParser(f, digest.doc_path(doc))
    return email

def test_subject():
    email = get_emlx_for_path(PATH_EMLX_LEGE)
    data = email.get_data()

    assert data['subject'] == "Re: promulgare lege"

def test_tree_with_attachments():
    email = get_emlx_for_path(PATH_EMLX_LEGE)
    tree = email.get_tree()

    headers = {'Subject', 'To', 'From', 'Date', 'Content-Type'}
    assert headers.issubset(set(tree['headers'].keys()))

    assert set(tree.keys()) == {'attachments', 'headers', 'parts'}
    assert len(tree['attachments']) == 2
    assert len(tree['parts']) == 4

def test_get_data():
    email = get_emlx_for_path(PATH_EMLX_LEGE)
    attach = email.get_data().get('attachments')

    assert len(attach) == 2
