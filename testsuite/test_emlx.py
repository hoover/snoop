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
