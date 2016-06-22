from maldini import digest, models, emails

MAIL_PATH_MAPBOX = "eml-1-promotional/Introducing Mapbox Android Services - " \
              "Mapbox Team <newsletter@mapbox.com> - 2016-04-20 1603.eml"
MAIL_PATH_CODINGAME = "eml-1-promotional/New on CodinGame: Check it out! - " \
                 "CodinGame <coders@codingame.com> - 2016-04-21 1034.eml"
MAIL_PATH_CAMPUS = "eml-2-attachment/FW: Invitation Fontys Open Day 2nd " \
                    "of February 2014 - Campus Venlo " \
                    "<campusvenlo@fontys.nl> - 2013-12-16 1700.eml"
MAIL_PATH_AMERICAN = "eml-3-uppercaseheaders/Fwd: The American College " \
                     "of Thessaloniki - Greece - Tarek Kouatly " \
                     "<tarek@act.edu> - 2013-11-11 1622.eml"
MAIL_PATH_LONG_FILENAMES = "eml-5-long-names/Attachments have " \
                           "long file names..eml"
MAIL_PATH_NO_SUBJECT = "eml-2-attachment/message-without-subject.eml"

def get_email_for_path(path):
    doc = models.Document(path=path)
    with digest.open_document(doc) as f:
        email = emails.EmailParser(f)
    return email

def test_subject():
    email = get_email_for_path(MAIL_PATH_MAPBOX)
    data = email.get_data()

    assert data['subject'] == "Introducing Mapbox Android Services"

def test_no_subject_or_text():
    email = get_email_for_path(MAIL_PATH_NO_SUBJECT)
    data = email.get_data()

    assert 'subject' in data
    assert len(data['subject']) == 0
    assert type(data['subject']) is str

    text = email.get_text()
    assert type(text) is str
    assert len(text) <= 2

def test_text():
    email_codin = get_email_for_path(MAIL_PATH_CODINGAME)
    assert email_codin.get_text().startswith("New on CodinGame: Check it out!")

    email_mapbox = get_email_for_path(MAIL_PATH_MAPBOX)
    assert "Android Services includes RxJava" in email_mapbox.get_text()

def test_people():
    email = get_email_for_path(MAIL_PATH_MAPBOX)
    data = email.get_data()

    assert type(data['to']) is list
    assert len(data['to']) == 1
    assert "penultim_o@yahoo.com" in data['to']

    assert type(data['from']) is str
    assert "Teamnewsletter@mapbox.com" in data['from']

def test_normal_attachments():
    email = get_email_for_path(MAIL_PATH_CAMPUS)
    attachments = email.get_data().get('attachments')

    assert attachments
    assert type(attachments) is dict
    assert len(attachments) == 2

def test_attachment_with_long_filename():
    email = get_email_for_path(MAIL_PATH_LONG_FILENAMES)
    attachments = email.get_data().get('attachments')

    assert len(attachments) == 3


