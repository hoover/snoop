from maldini import models, emails

PATH_EMLX_LEGE = "lists.mbox/F2D0D67E-7B19-4C30-B2E9-" \
                 "B58FE4789D51/Data/1/Messages/1498.partial.emlx"

def parse_email(path):
    doc = models.Document(path=path, content_type='message/x-emlx')
    return emails.parse_email(doc)

def test_subject():
    data = parse_email(PATH_EMLX_LEGE)
    assert data['subject'] == "Re: promulgare lege"

def test_tree_with_attachments():
    data = parse_email(PATH_EMLX_LEGE)
    tree = data['tree']

    headers = {'subject', 'to', 'from', 'date', 'content-type'}
    assert headers.issubset(set(tree['headers'].keys()))

    assert set(tree.keys()) == {'attachments', 'headers', 'parts'}
    assert len(tree['attachments']) == 2
    assert len(tree['parts']) == 4

def test_get_data():
    data = parse_email(PATH_EMLX_LEGE)
    attach = data.get('attachments')
    assert len(attach) == 2
