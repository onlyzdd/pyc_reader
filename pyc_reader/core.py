import sys

from .base import Buffer, PythonVersion


class PycFile:
    def __init__(self, file: str) -> None:
        self._buffer = Buffer.from_file(file=file)
        self.parse()

    def parse(self) -> None:
        self.parse_header()
        self.parse_body()

    def parse_header(self) -> None:
        '''Parse PYC file header
        version >= 4.0: unsupported
        version >= 3.7: magic u4, flags u4, [source_hash b8 | (source_mtime u4, source_size u4)]
        version >= 3.3: magic u4, source_mtime u4, source_size u4
        otherwise: magic u4, source_mtime u4
        '''
        self.magic = self._buffer.read_uint16()
        self.version = PythonVersion.from_magic(self.magic)
        crlf = self._buffer.read(2)
        assert crlf == b'\r\n'
        if self.version >= PythonVersion(4, 0):
            raise Exception(f'Unsupported Python version {self.version}')
        if self.version >= PythonVersion(3, 7):
            self.flags = self._buffer.read_uint32()
            if self.flags & ~0b11:
                raise Exception(f'Invalid flags {self.flags!r}')
            self.hash_based = self.flags & 0b1 != 0
            if self.hash_based:
                self.checksource = self.flags & 0b10 != 0
                self.source_hash = self._buffer.read(8)
            else:
                self.source_mtime = self._buffer.read_uint32()
                self.source_size = self._buffer.read_uint32()
        elif self.version >= PythonVersion(3, 3):
            self.source_mtime = self._buffer.read_uint32()
            self.source_size = self._buffer.read_uint32()
        else:
            self.source_mtime = self._buffer.read_uint32()
        self.header_length = self._buffer.tell()

    def parse_body(self) -> None:
        if self.version == PythonVersion(2, 7):
            self.parse_py27()
        elif self.version == PythonVersion(3, 5):
            self.parse_py35()
        elif self.version == PythonVersion(3, 6):
            self.parse_py36()
        elif self.version == PythonVersion(3, 7):
            self.parse_py37()
        else:
            print('Not support yet.')
        assert self._buffer.end()

    def parse_py27(self) -> None:
        '''Python2.7'''
        from pyc_reader.py27 import parse as parse_27
        self.body = parse_27(self._buffer)

    def parse_py35(self) -> None:
        '''Python3.5'''
        from pyc_reader.py35 import parse as parse_35
        self.body = parse_35(self._buffer)

    def parse_py36(self) -> None:
        '''Python3.6'''
        self.body = None
    
    def parse_py37(self) -> None:
        from pyc_reader.py35 import parse as parse_35
        self.body = parse_35(self._buffer)

    def get_source(self) -> str:
        if self.version.major == sys.version_info.major and self.version.minor == sys.version_info.minor:
            import inspect
            import marshal
            return inspect.getsource(marshal.loads(self._buffer.read_at(self.header_length)))
        else:
            raise Exception(f'Unable to get source due to mismatched Python versions, please try run you code with Python {self.version}')
