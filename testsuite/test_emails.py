def test_subject():
    from maldini import models, digest, emails

    doc = models.Document(path='eml-1-promotional/'
        'Introducing Mapbox Android Services - Mapbox Team '
        '<newsletter@mapbox.com> - 2016-04-20 1603.eml')

    with digest.open_document(doc) as f:
        email = emails.EmailParser(f)
    data = email.get_data()

    assert data['subject'] == "Introducing Mapbox Android Services"
