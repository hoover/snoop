import pytest
from snoop import models, emails

pytestmark = [
    pytest.mark.skip("Model refactoring"),
]

PATH_EMLX_LEGE = "lists.mbox/F2D0D67E-7B19-4C30-B2E9-" \
                 "B58FE4789D51/Data/1/Messages/1498.partial.emlx"

def parse_email(path, collection):
    doc = models.Document(
        path=path,
        content_type='message/x-emlx',
        collection=collection,
    )
    return emails.parse_email(doc)

def test_subject(document_collection):
    data = parse_email(PATH_EMLX_LEGE, document_collection)
    assert data['subject'] == "Re: promulgare lege"

def test_tree_with_attachments(document_collection):
    data = parse_email(PATH_EMLX_LEGE, document_collection)
    tree = data['tree']

    headers = {'subject', 'to', 'from', 'date', 'content-type'}
    assert headers.issubset(set(tree['headers'].keys()))

    assert set(tree.keys()) == {'headers', 'parts'}
    assert len(data['attachments']) == 2
    assert len(tree['parts']) == 4

def test_get_data(document_collection):
    data = parse_email(PATH_EMLX_LEGE, document_collection)
    attach = data.get('attachments')
    assert len(attach) == 2
