import configparser as ConfigParser
import io
import re

# override configparser load method
class ConfParsAdapter(io.RawIOBase):
    @staticmethod
    def _confParsAdapter(fd):
        num=1
        rxsec = re.compile('\[.*\]( *#.*)?$')
        rxkv = re.compile('.+?=.*')
        rxvoid = re.compile('(#.*)?$')
        for line in fd:
            if rxsec.match(line.strip()):
                num=1
            elif rxkv.match(line) or rxvoid.match(line.strip()):
                pass
            else:
                line = 'line{}={}'.format(num, line)
                num += 1
            yield(line)

    def __init__(self, fd):
        self.fd = self._confParsAdapter(fd)
    def readline(self, hint = -1):
        try:
            return next(self.fd)
        except StopIteration:
            return ""
