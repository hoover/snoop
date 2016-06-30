def chunks(file, blocksize=65536):
    while True:
        data = file.read(blocksize)
        if not data:
            return
        yield data

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
