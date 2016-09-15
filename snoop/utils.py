import subprocess
import re

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
