import subprocess
import re


class Magic:

    def __init__(self):
        self.process = subprocess.Popen(
            ['file', '-', '--mime-type', '--mime-encoding'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )

    def finish(self):
        if self.process:
            self.process.stdin.close()
            output = self.process.stdout.read().decode('latin1')
            m = re.match(
                r'/dev/stdin: (?P<mime_type>[^;].+); '
                r'charset=(?P<mime_encoding>\S+)',
                output,
            )
            self.result = (m.group('mime_type'), m.group('mime_encoding'))
            assert self.process.wait() == 0
            self.process = None

    def update(self, buffer):
        if not self.process:
            return

        try:
            self.process.stdin.write(buffer)
        except IOError:
            self.finish()

    def get_result(self):
        self.finish()
        return self.result
