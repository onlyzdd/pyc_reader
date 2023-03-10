'''
Parser for PYC files generated by Python 2.7
'''
from dataclasses import dataclass

from .base import Buffer, ObjectType, PycBuffer, PyAssembly, PyObject, PyFalse, PyNone, PyTrue, PyInt

@dataclass
class PyCode:
    co_argcount: int = 0,
    n_locals: int = 0,
    n_stacksize: int = 0,
    co_flags: int = 4,
    co_code: PyAssembly = None,
    co_consts: PyObject = None,
    co_names: PyObject = None,
    co_varnames: PyObject = None,
    co_freevars: PyObject = None,
    co_cellvars: PyObject = None,
    co_filename: PyObject = None,
    co_name: PyObject = None,
    co_firstlineno: int = None,
    co_lnotab: PyObject = None


class PycBuffer27(PycBuffer):
    def __init__(self, buffer: Buffer) -> None:
        super().__init__(buffer)

    
    def read_code(self) -> PyCode:
        return PyCode(
            co_argcount=self.buffer.read_uint32(),
            n_locals=self.buffer.read_uint32(),
            n_stacksize=self.buffer.read_uint32(),
            co_flags=self.buffer.read_uint32(),
            co_code=self.read_assembly(),
            co_consts=self.read_pyobject(),
            co_names=self.read_pyobject(),
            co_varnames=self.read_pyobject(),
            co_freevars=self.read_pyobject(),
            co_cellvars=self.read_pyobject(),
            co_filename=self.read_pyobject(),
            co_name=self.read_pyobject(),
            co_firstlineno=self.buffer.read_uint32(),
            co_lnotab=self.read_pyobject()
        )
    

    def read_pyobject(self) -> PyObject:
        object_type = self.buffer.read_uint8()
        if object_type == ObjectType.TYPE_TUPLE:
            object_value = self.read_tuple()
        elif object_type == ObjectType.TYPE_FALSE:
            object_value = PyFalse()
        elif object_type == ObjectType.TYPE_NONE:
            object_value = PyNone()
        elif object_type == ObjectType.TYPE_STRING_REF:
            object_value = self.read_string_ref()
        elif object_type == ObjectType.TYPE_TRUE:
            object_value = PyTrue()
        elif object_type == ObjectType.TYPE_CODE:
            object_value = self.read_code()
        elif object_type == ObjectType.TYPE_INT:
            object_value = PyInt(self.buffer.read_uint32())
        elif object_type == ObjectType.TYPE_STRING:
            object_value = self.read_string()
        elif object_type == ObjectType.TYPE_INTERNED:
            object_value = self.read_interned()
        elif object_type == ObjectType.TYPE_UNICODE_STRING:
            object_value = self.read_unicode_string()
        else:
            raise Exception(f'Wrong object type met: {object_type} "{chr(object_type)}"')
        return PyObject(object_type, object_value)


def parse(buffer: Buffer) -> PyObject:
    return PycBuffer27(buffer).read_pyobject()
