from maldini import digest, models, emails

MAIL_PATH_MAPBOX = "eml-1-promotional/Introducing Mapbox Android Services - " \
              "Mapbox Team <newsletter@mapbox.com> - 2016-04-20 1603.eml"
MAIL_PATH_CODINGAME = "eml-1-promotional/New on CodinGame: Check it out! - " \
                 "CodinGame <coders@codingame.com> - 2016-04-21 1034.eml"
MAIL_PATH_CAMPUS = "eml-2-attachment/FW: Invitation Fontys Open Day 2nd " \
                    "of February 2014 - Campus Venlo " \
                    "<campusvenlo@fontys.nl> - 2013-12-16 1700.eml"

def test_subject():
    doc = models.Document(path=MAIL_PATH_MAPBOX)

    with digest.open_document(doc) as f:
        email = emails.EmailParser(f)
    data = email.get_data()

    assert data['subject'] == "Introducing Mapbox Android Services"
