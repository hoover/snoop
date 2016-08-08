import mimetypes

mimetypes.add_type('message/x-emlx', '.emlx')
mimetypes.add_type('message/x-emlxpart', '.emlxpart')
mimetypes.add_type('application/vnd.ms-outlook', '.msg')
mimetypes.add_type('application/x-pgp-encrypted-ascii', '.asc')
mimetypes.add_type('application/x-pgp-encrypted-binary', '.pgp')


def guess_content_type(filename):
    return mimetypes.guess_type(filename, strict=False)[0] or ''


FILE_TYPES = {
    'application/x-directory': 'folder',
    'application/pdf': 'pdf',
    'text/plain': 'text',
    'text/html': 'html',
    'message/x-emlx': 'email',
    'message/rfc822': 'email',
    'application/vnd.ms-outlook': 'email',

    'application/msword': 'doc',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'doc',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.template': 'doc',
    'application/vnd.ms-word.document.macroEnabled.12': 'doc',
    'application/vnd.ms-word.template.macroEnabled.12': 'doc',
    'application/vnd.oasis.opendocument.text': 'doc',
    'application/vnd.oasis.opendocument.text-template': 'doc',
    'application/rtf': 'doc',

    'application/vnd.ms-excel': 'xls',
    'application/vnd.openxlsformats-officedocument.spreadsheetml.sheet': 'xls',
    'application/vnd.openxlsformats-officedocument.spreadsheetml.template': 'xls',
    'application/vnd.ms-excel.sheet.macroEnabled.12': 'xls',
    'application/vnd.ms-excel.template.macroEnabled.12': 'xls',
    'application/vnd.ms-excel.addin.macroEnabled.12': 'xls',
    'application/vnd.ms-excel.sheet.binary.macroEnabled.12': 'xls',
    'application/vnd.oasis.opendocument.spreadsheet-template': 'xls',
    'application/vnd.oasis.opendocument.spreadsheet': 'xls',

    'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'ppt',
    'application/vnd.openxmlformats-officedocument.presentationml.template': 'ppt',
    'application/vnd.openxmlformats-officedocument.presentationml.slideshow': 'ppt',
    'application/vnd.ms-powerpoint.addin.macroEnabled.12': 'ppt',
    'application/vnd.ms-powerpoint.presentation.macroEnabled.12': 'ppt',
    'application/vnd.ms-powerpoint.template.macroEnabled.12': 'ppt',
    'application/vnd.ms-powerpoint.slideshow.macroEnabled.12': 'ppt',
    'application/vnd.oasis.opendocument.presentation': 'ppt',
    'application/vnd.oasis.opendocument.presentation-template': 'ppt',

    'application/zip': 'archive',
    'application/rar': 'archive',
    'application/x-7z-compressed': 'archive',
    'application/x-tar': 'archive',
    'application/x-bzip2': 'archive',
    'application/x-zip': 'archive',
    'application/x-gzip': 'archive',
    'application/x-zip-compressed': 'archive',
    'application/x-rar-compressed': 'archive',
}


def guess_filetype(doc):
    content_type = doc.content_type.split(';')[0]
    return FILE_TYPES.get(content_type)
