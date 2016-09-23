import subprocess
import re
import exifread
from datetime import datetime
import fcntl
import json
from datetime import datetime, timezone
from time import time
from pathlib import Path
from functools import wraps
from contextlib import contextmanager
from django.conf import settings


def extract_gps_location(tags):
    def ratio_to_float(ratio):
        return float(ratio.num) / ratio.den

    def convert(value):
        d = ratio_to_float(value.values[0])
        m = ratio_to_float(value.values[1])
        s = ratio_to_float(value.values[2])
        return d + (m / 60.0) + (s / 3600.0)

    tags = {key: tags[key] for key in tags.keys() if key.startswith('GPS')}

    lat = tags.get('GPS GPSLatitude')
    lat_ref = tags.get('GPS GPSLatitudeRef')
    lng = tags.get('GPS GPSLongitude')
    lng_ref = tags.get('GPS GPSLongitudeRef')

    if any(v is None for v in [lat, lat_ref, lng, lng_ref]):
        return None

    lat = convert(lat)
    if lat_ref.values[0] != 'N':
        lat = -lat
    lng = convert(lng)
    if lng_ref.values[0] != 'E':
        lng = -lng
    return "{}, {}".format(lat, lng)

def convert_exif_date(str):
    try:
        date = datetime.strptime(str, "%Y:%m:%d %H:%M:%S")
    except ValueError:
        return None
    return date.isoformat()

def extract_exif(doc):
    # detauls=False removes thumbnails and MakerNote (manufacturer specific
    # information). See https://pypi.python.org/pypi/ExifRead#tag-descriptions
    with doc.open(filesystem=True) as f:
        tags = exifread.process_file(f, details=False)
    if not tags:
        return {}

    data = {}
    gps = extract_gps_location(tags)
    if gps:
        data['location'] = gps

    for key in ['EXIF DateTimeOriginal', 'Image DateTime']:
        if key in tags:
            date = convert_exif_date(str(tags[key]))
            if date:
                data['date-created'] = date
                break

    return data

def word_count(text):
    words = re.findall(r'\w+', text)
    return len(words)

def chunks(file, blocksize=65536):
    while True:
        data = file.read(blocksize)
        if not data:
            return
        yield data

def pdftotext(input):
    return subprocess.check_output(['pdftotext', '-', '-'], stdin=input)

def build_raw_query(table, where):
    """Build a raw SQL query with a user-defined `where` clause."""
    return " ".join([
        'SELECT', 'id', 'FROM', table,
        'WHERE', where.replace('%', '%%'),
    ])

def timeit(name):
    """ Measure aggregate time for a function or code block

    .. sourcode:: python

        @timeit('emails')
        def parse_email(doc):
            do_stuff()

    .. sourcode:: python

        emails_timer = timeit('emails')
        for _ in range(10):
            with emails_timer.cm():
                do_stuff()
    """
    import sys, atexit, time
    total = 0

    @atexit.register
    def report():
        print("{}: {:.3f}".format(name, total), file=sys.stderr)

    @contextmanager
    def cm():
        nonlocal total
        t0 = time.time()
        try:
            yield
        finally:
            total += time.time() - t0

    def decorator(func):
        def wrapper(*args, **kwargs):
            with cm():
                return func(*args, **kwargs)

        return wrapper

    decorator.cm = cm

    return decorator

@contextmanager
def flock(fd):
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield fd
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)

def append_with_lock(path, bytes):
    with open(path, 'ab') as file:
        with flock(file) as locked:
            locked.write(bytes.encode('utf-8'))

def log_result(extra_data=None):
    """
    Wrapps a function to log the result of running it. The function should
    return a dict with serializable data.

    :arg extra_data: a dict with additional data to be added to the log
        message.
    """

    if settings.SNOOP_LOG_DIR is None:
        def decorate_without_log(fn):
            return fn
        return decorate_without_log

    def decorate_with_log(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            time_stared = datetime.now(timezone.utc).astimezone().isoformat()

            t0 = time()
            fn_result = fn(*args, **kwargs)
            duration = time() - t0

            if not extra_data:
                data = dict(fn_result.items())
            else:
                data = dict(extra_data.items())
                data.update(fn_result)
            data['ok'] = 'error' not in data
            data['started'] = time_stared
            data['duration'] = duration

            log_line = json.dumps(data) + '\n'
            day = datetime.utcfromtimestamp(t0).date().isoformat()
            logfile = Path(settings.SNOOP_LOG_DIR) / (day + '.txt')
            logfile_path = str(logfile.absolute())
            append_with_lock(logfile_path, log_line)
            return fn_result
        return wrapped
    return decorate_with_log
