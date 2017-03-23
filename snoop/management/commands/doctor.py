from pathlib import Path
import subprocess
import re
import sys
import urllib.request
import urllib.error
import json
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connections
from django.db.utils import OperationalError

ELASTICSEARCH_MIN_VERSION = (2, 0, 0)
ELASTICSEARCH_MAX_VERSION = (2, 4, 4)
PST_MIN_VERSION = (0, 2, 0)
TIKA_MIN_VERSION = (1, 13)


def path_exists(path):
    return Path(path).exists()


def http_get_content(link):
    try:
        with urllib.request.urlopen(link) as content:
            return content.read()
    except (urllib.error.HTTPError, urllib.error.URLError):
        return None


def get_version(exe_path, version_argument='--version',
                regex=r'([\d\.]+)', check_output=True,
                is_numeric=True):
    if check_output:
        output = subprocess.check_output([exe_path, version_argument])
    else:
        completed = subprocess.run(
            [exe_path, version_argument],
            check=False,
            stderr=subprocess.STDOUT,
            stdout=subprocess.PIPE)
        output = completed.stdout
    string_output = str(output)

    matches = re.search(regex, string_output, re.MULTILINE)
    if not matches:
        return None

    if is_numeric:
        return tuple(int(x) for x in matches.group(1).split("."))
    return matches.group(1)


class Command(BaseCommand):
    help = "Sanity check for snoop. Run with no arguments."

    def handle(self, *args, **options):
        checkers = [
            ('python', self.check_python, False),
            ('database', self.check_database, False),
            ('elasticsearch', self.check_es, False),
            ('msgconvert', self.check_msgconvert, settings.SNOOP_MSGCONVERT_SCRIPT is None),
            ('readpst', self.check_readpst, settings.SNOOP_READPST_BINARY is None),
            ('Apache Tika', self.check_tika, settings.SNOOP_TIKA_SERVER_ENDPOINT is None),
            ('7z', self.check_7z, settings.SNOOP_SEVENZIP_BINARY is None),
            ('gpg', self.check_gpg, settings.SNOOP_GPG_BINARY is None),
        ]

        have_errors = False
        for name, check_fun, skip in checkers:
            if skip:
                self.print_message("Skipping the check for " + name + ".")
            else:
                self.print_message("Checking " + name + ".")
                result = check_fun()
                if result:
                    self.print_success(' ' * 9 + name + " ok.")
                else:
                    have_errors = True
                    self.print_error(name + " failed the check.")
            self.print_message('')

        if have_errors:
            self.print_error("The setup has failed some checks.")
            self.print_error("For more information please see")
            self.print_error("https://github.com/hoover/snoop/blob/master/Readme.md")
            sys.exit(1)
        else:
            self.print_success("All checks have passed.")

    def check_python(self):
        if sys.version_info[0] != 3 or sys.version_info[1] < 5:
            self.print_error("The Python version supplied is {}.".format(sys.version))
            self.print_error("Hoover needs at least Python 3.5 to work.")
            self.print_error("Please use a supported version of Python.")
            return False
        return True

    def check_database(self):
        db_conn = connections['default']
        try:
            c = db_conn.cursor()
        except OperationalError:
            self.print_error("The database settings are not valid.")
            self.print_error("Please check the database access data under DATABASES.")
            return False
        return True

    def check_msgconvert(self):
        msgconvert_path = settings.SNOOP_MSGCONVERT_SCRIPT
        if not path_exists(msgconvert_path):
            self.print_error("You enabled msgconvert support but")
            self.print_error("SNOOP_MSGCONVERT_SCRIPT is not set to a valid path.")
            return False

        version = get_version(msgconvert_path, '--help', regex='(msgconvert)',
                              check_output=False, is_numeric=False)
        if not version:
            self.print_error("Could run the script provided in SNOOP_MSGCONVERT_SCRIPT")
            return False

        cache_dir = settings.SNOOP_MSG_CACHE
        if not cache_dir or not Path(cache_dir).is_dir():
            self.print_error("SNOOP_MSG_CACHE does not point to a valid directory.")
            return False
        return True

    def check_readpst(self):
        readpst_path = settings.SNOOP_READPST_BINARY
        if not path_exists(readpst_path):
            self.print_error("You enabled readpst support but")
            self.print_error("SNOOP_READPST_BINARY is not set to a valid path.")
            return False

        version = get_version(readpst_path, '-V')
        if not version:
            self.print_error("Failed to check the readpst version.")
            self.print_error("Please check if SNOOP_READPST_BINARY points to a valid executable.")
            return False

        if version < PST_MIN_VERSION:
            self.print_error("Please install a more recent version of readpst.")
            return False

        cache_dir = settings.SNOOP_PST_CACHE_ROOT
        if not cache_dir or not Path(cache_dir).is_dir():
            self.print_error("SNOOP_PST_CACHE_ROOT does not point to a valid directory.")
            return False
        return True

    def check_es(self):
        es_link = settings.SNOOP_ELASTICSEARCH_URL
        content = http_get_content(es_link)

        if not content:
            self.print_error("Could not connect to elasticsearch using")
            self.print_error("the link supplied in SNOOP_ELASTICSEARCH_URL.")
            return False

        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            self.print_error("elasticsearch's response could not be decoded.")
            self.print_error("Please restart the elasticsearch server and try again.")
            return False

        version_string = data['version']['number']
        version_string = re.sub(r'[^\d\.]+', '', version_string)
        version = tuple(int(x) for x in version_string.split('.'))

        if not ELASTICSEARCH_MIN_VERSION < version < ELASTICSEARCH_MAX_VERSION:
            self.print_error("elasticsearch is version {}, but".format(version))
            self.print_error("Hoover needs elasticsearch to be in between versions")
            self.print_error("{} and {}".format(ELASTICSEARCH_MIN_VERSION,
                                                ELASTICSEARCH_MAX_VERSION))
            return False
        return True

    def check_tika(self):
        tika_link = settings.SNOOP_TIKA_SERVER_ENDPOINT
        content = http_get_content(tika_link + "/version")
        if not content:
            self.print_error("Could not connect to Apache Tika using")
            self.print_error("the link supplied in SNOOP_TIKA_SERVER_ENDPOINT.")
            return False

        version_string = str(content)
        matches = re.search('([\d\.]+)', version_string, re.MULTILINE)
        if not matches:
            self.print_error("Apache Tika's response did not contain a valid version number.")
            self.print_error("Please restart the Apache Tika server and try again.")
            return False

        version_string = matches.group(1)
        version = tuple(int(x) for x in version_string.split('.'))

        if version < TIKA_MIN_VERSION:
            self.print_error("tika is version {}, but")
            self.print_error("Hoover needs tika to be at least version {}".format(TIKA_MIN_VERSION))
            self.print_error("Download tika from https://tika.apache.org/download")
            return False
        return True

    def check_7z(self):
        seven_zip_path = settings.SNOOP_SEVENZIP_BINARY
        if not path_exists(seven_zip_path):
            self.print_error("You enabled 7z support but")
            self.print_error("SNOOP_SEVENZIP_BINARY is not set to a valid path.")
            return False

        version = get_version(seven_zip_path, '--help', r'Version +([\d\.]+)', is_numeric=False)
        if not version:
            self.print_error("Failed to check the version for 7z.")
            self.print_error("Please check if SNOOP_SEVENZIP_BINARY points to a valid executable.")
            return False

        cache_dir = settings.SNOOP_ARCHIVE_CACHE_ROOT
        if not cache_dir or not Path(cache_dir).is_dir():
            self.print_error("SNOOP_ARCHIVE_CACHE_ROOT does not point to a valid directory.")
            return False
        return True

    def check_gpg(self):
        gpg_path = settings.SNOOP_GPG_BINARY
        if not path_exists(gpg_path):
            self.print_error("You enabled gpg support but")
            self.print_error("SNOOP_GPG_BINARY is not set to a valid path.")
            return False

        version = get_version(gpg_path)
        if not version:
            self.print_error("Failed to check the version for gpg.")
            self.print_error("Please check if SNOOP_GPG_BINARY points to a valid executable.")
            return False

        cache_dir = settings.SNOOP_GPG_HOME
        if not cache_dir or not Path(cache_dir).is_dir():
            self.print_error("SNOOP_GPG_HOME does not point to a valid directory.")
            return False
        return True

    def print_error(self, string):
        self.stdout.write(self.style.ERROR(string))

    def print_message(self, string):
        self.stdout.write(string)

    def print_success(self, string):
        self.stdout.write(self.style.SUCCESS(string))
