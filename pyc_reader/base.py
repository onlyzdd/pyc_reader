import bisect
from dataclasses import dataclass
from enum import IntEnum
from opcode import opmap
from typing import Any, List, Literal, Union


@dataclass(order=True)
class PythonVersion:
    major: int
    minor: int
    micro: int = 0

    @classmethod
    def from_magic(cls, magic: int):
        assert magic >= 3000, f'Bad magic number: {magic}'
        magic_numbers = sorted(versions.keys())
        idx = bisect.bisect_left(magic_numbers, magic) - 1
        return versions[magic_numbers[idx]]

    def __repr__(self) -> str:
        return f'PythonVersion({self.major}, {self.minor}, {self.micro})'

    def __str__(self) -> str:
        return f'{self.major}.{self.minor}.{self.micro}'


versions = {
    3000: PythonVersion(3, 0),
    3141: PythonVersion(3, 1),
    3160: PythonVersion(3, 2),
    3190: PythonVersion(3, 3),
    3250: PythonVersion(3, 4),
    3320: PythonVersion(3, 5),
    3360: PythonVersion(3, 6),
    3390: PythonVersion(3, 7),
    3400: PythonVersion(3, 8),
    3420: PythonVersion(3, 9),
    3430: PythonVersion(3, 10),
    3450: PythonVersion(3, 11),
    3550: PythonVersion(3, 12),
    20121: PythonVersion(1, 5),
    62171: PythonVersion(2, 7),
}

class ObjectType(IntEnum):
    TYPE_TUPLE = 40
    TYPE_SMALL_TUPLE = 41
    TYPE_FALSE = 70
    TYPE_NONE = 78
    TYPE_STRING_REF = 82
    TYPE_TRUE = 84
    TYPE_SHORT_ASCII_INTERNED = 90
    TYPE_CODE = 99
    TYPE_BINARY_FLOAT = 103
    TYPE_INT = 105
    TYPE_REF = 114
    TYPE_STRING = 115
    TYPE_INTERNED = 116
    TYPE_UNICODE_STRING = 117
    TYPE_SHORT_ASCII = 122
    FLAG_REF = 128

    @classmethod
    def has_value(cls, value: int) -> bool:
        return value in cls._value2member_map_

@dataclass
class PyOpArg:
    opcode: int
    oparg: Union[int, None] = None

@dataclass
class PyAssembly:
    length: int
    items: List[PyOpArg] = None

@dataclass
class PyTuple:
    length: int
    items: List['PyObject'] = None

@dataclass
class PyFalse:
    pass


@dataclass
class PyNone:
    pass


@dataclass
class PyStringRef:
    index: int


@dataclass
class PyTrue:
    pass


@dataclass
class PyInt:
    value: int

@dataclass
class PyString:
    length: int
    data: bytes

@dataclass
class PyInterned:
    length: int
    data: str

@dataclass
class PyUnicodeString:
    length: int
    data: str

@dataclass
class PyObject:
    object_type: int
    object_value: Any


class Buffer:
    def __init__(self, stream: Union[bytearray, bytes]) -> None:
        self.idx = 0
        self.stream = stream
    
    @classmethod
    def from_file(cls, file):
        with open(file, 'rb') as fp:
            return cls(fp.read()) 

    def seek(self, idx: int) -> None:
        self.idx = idx

    def tell(self) -> int:
        return self.idx
    
    def read(self, n_bytes: int = 0):
        if n_bytes > 0:
            data = self.stream[self.idx:self.idx + n_bytes]
            self.idx += n_bytes
            return data
        else:
            data = self.stream[self.idx:]
            self.idx = len(self.stream)
            return data

    def read_at(self, idx: int = 0, n_bytes: int = 0):
        if n_bytes > 0:
            return self.stream[idx:idx + n_bytes]
        return self.stream[idx:]

    def read_uint8(self):
        return int.from_bytes(self.read(1))

    def read_uint16(self, byteorder: Literal['little', 'big'] = 'little'):
        return int.from_bytes(self.read(2), byteorder=byteorder)

    def read_uint32(self, byteorder: Literal['little', 'big'] = 'little'):
        return int.from_bytes(self.read(4), byteorder=byteorder)

    def __len__(self) -> int:
        return len(self.stream)
    
    def end(self) -> bool:
        return self.idx >= len(self.stream)


class PycBuffer:
    def __init__(self, buffer: Buffer) -> None:
        self.buffer = buffer

    def read_tuple(self) -> PyTuple:
        length = self.buffer.read_uint32()
        items = [self.read_pyobject() for _ in range(length)]
        return PyTuple(length, items)
    
    def read_string_ref(self):
        return PyStringRef(self.buffer.read_uint32())

    def read_string(self):
        length = self.buffer.read_uint32()
        return PyString(
            length,
            self.buffer.read(length)
        )
    
    def read_interned(self):
        length = self.buffer.read_uint32()
        return PyInterned(length, self.buffer.read(length).decode('utf-8'))
    
    def read_unicode_string(self):
        length = self.buffer.read_uint32()
        return PyUnicodeString(length, self.buffer.read(length).decode('utf-8'))

    def read_assembly(self) -> PyAssembly:
        string_magic = self.buffer.read(1)
        assert string_magic == b's'
        length = self.buffer.read_uint32()
        items = []
        idx = 0
        while idx < length:
            opcode = self.buffer.read_uint8()
            idx += 1
            if opcode >= opmap['STORE_NAME']:
                idx += 2
                items.append(PyOpArg(opcode, self.buffer.read_uint16()))
            else:
                items.append(PyOpArg(opcode))
        return PyAssembly(length, items)
