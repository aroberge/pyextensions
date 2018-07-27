"""Swapping BINARY_ADD and BINARY_MULTIPLY

Note: If code contains something like a + b, or a * b, where
a and b are integer literals (e.g. 2 + 4), the operations are
done prior to the creation of a code object and thus are"""

from types import CodeType
import dis

ADD = dis.opmap['BINARY_ADD']
MUL = dis.opmap['BINARY_MULTIPLY']


def swap_add_mul(bytecode):
    new_bc = []
    for b in bytecode:
        if b == ADD:
            new_bc.append(MUL)
        elif b == MUL:
            new_bc.append(ADD)
        else:
            new_bc.append(b)
    return bytes(new_bc)


def create_new_co(code_object):
    new_code = swap_add_mul(code_object.co_code)
    new_const = []
    for c in code_object.co_consts:
        if isinstance(c, CodeType):
            new_const.append(create_new_co(c))
        else:
            new_const.append(c)
    new_code_object = CodeType(
        code_object.co_argcount,
        code_object.co_kwonlyargcount,
        code_object.co_nlocals,
        code_object.co_stacksize,
        code_object.co_flags,
        new_code,
        tuple(new_const),
        code_object.co_names,
        code_object.co_varnames,
        code_object.co_filename,
        code_object.co_name,
        code_object.co_firstlineno,
        code_object.co_lnotab,
        code_object.co_freevars,
        code_object.co_cellvars,
    )
    return new_code_object


def transform_bytecode(code_object):
    new_co = create_new_co(code_object)
    return new_co
