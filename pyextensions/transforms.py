"""This module takes care of identifying, importing and adding source
code transformers. It also contains a function, `transform`, which
takes care of invoking all known transformers to convert a source code.
"""
import ast
import io
import sys

from . import unparse

def my_unparse(tree):
    v = io.StringIO()
    unparse.Unparser(tree, file=v)
    return v.getvalue()


class NullTransformer:
    """NullTransformer is a convenience class which can generate instances
    to be used when a given transformer cannot be imported."""

    def transform_source(self, source):
        return source

TRANSFORMERS = {}
AST_TRANSFORMERS = []


def add_transformers(line):
    """Extract the transformers names from a line of code of the form
       #ext transformer1 [transformer2]
       and adds them to the globally known dict
    """
    assert line.startswith("#ext ")
    line = line[5:]

    for trans in line.split(" "):
        import_transformer(trans.strip())


def import_transformer(name):
    """If needed, import a transformer, and adds it to the globally known dict
       The code inside a module where a transformer is defined should be
       standard Python code, which does not need any transformation.
       So, we disable the import hook, and let the normal module import
       do its job - which is faster and likely more reliable than our
       custom method.
    """
    if name in TRANSFORMERS:
        if not name in AST_TRANSFORMERS:
            if hasattr(TRANSFORMERS[name], 'transform_ast'):
                AST_TRANSFORMERS.append(name)
        return TRANSFORMERS[name]

    # We are adding a transformer built from normal/standard Python code.
    # As we are not performing transformations, we temporarily disable
    # our import hook, both to avoid potential problems AND because we
    # found that this resulted in much faster code.
    hook = sys.meta_path[0]
    sys.meta_path = sys.meta_path[1:]
    try:
        TRANSFORMERS[name] = __import__(name)
        # Some transformers are not allowed in the console.
        # If an attempt is made to activate one of them in the console,
        # we replace it by a transformer that does nothing and print a
    # message specific to that transformer as written in its module.
        if hasattr(TRANSFORMERS[name], 'transform_ast'):
            AST_TRANSFORMERS.append(name)
    except ImportError:
        sys.stderr.write(
            "Warning: Import Error in add_transformers: %s not found\n" % name
        )
        TRANSFORMERS[name] = NullTransformer()
    except Exception as e:
        sys.stderr.write(
            "\nUnexpected exception in transforms.import_transformer %s\n "
            % e.__class__.__name__
        )
        sys.stderr.write(str(e.args))
        sys.stderr.write(f"\nname = {name}\n")
    finally:
        sys.meta_path.insert(0, hook)  # restore import hook

    return TRANSFORMERS[name]


def identify_requested_transformers(source):
    """
    Scan a source for lines of the form::

        #ext transformer1 [transformer2 ...]

    identifying transformers to be used and ensure that they are imported.
    """
    lines = source.split("\n")
    linenumbers = []
    clear = False
    for number, line in enumerate(lines):
        if line.startswith("#ext "):
            if not clear:
                TRANSFORMERS.clear()
                AST_TRANSFORMERS.clear()
                clear = True
            add_transformers(line)
    return None


def add_all_imports(source):
    """Some transformers may require that other modules be imported
    in the source code for it to work properly.
    """
    for name in TRANSFORMERS:
        tr_module = import_transformer(name)
        if hasattr(tr_module, 'add_import'):
            source = tr_module.add_import() + source

    return source



def apply_source_transformations(source):
    """Used to convert the source code, making use of known transformers.

       "transformers" are modules which must contain a function

           transform_source(source)

       which returns a tranformed source.
       Some transformers (for example, those found in the standard library
       module lib2to3) cannot cope with non-standard syntax; as a result, they
       may fail during a first attempt. We keep track of all failing
       transformers and keep retrying them until either they all succeeded
       or a fixed set of them fails twice in a row.
    """
    # Some transformer fail when multiple non-Python constructs
    # are present. So, we loop multiple times keeping track of
    # which transformations have been unsuccessfully performed.
    not_done = TRANSFORMERS
    while True:
        failed = {}
        for name in not_done:
            tr_module = import_transformer(name)
            if hasattr(tr_module, 'transform_source'):
                try:
                    source = tr_module.transform_source(source)
                except Exception as e:
                    failed[name] = tr_module

        if not failed:
            break

        # If the exact same set of transformations are not performed
        # twice in a row, there is no point in trying out again.
        if failed == not_done:
            print("Warning: the following source transformations could not be done:")
            for key in failed:
                print(key)
            break
        not_done = failed  # attempt another pass

    return source


def apply_ast_transformations(source):
    """Used to convert the source code into an AST tree and applying
       all AST transformer specified in the source code. It returns
       a (potentially transformed) AST tree.

       "AST transformers" are modules which must contain a function

           transform_ast(tree)

       which return another AST tree.
    """
    if not AST_TRANSFORMERS:
        return source
    tree = ast.parse(source)
    for name in AST_TRANSFORMERS:
        tr_module = TRANSFORMERS[name]
        try:
            tree = tr_module.transform_ast(tree)
        except Exception as e:
            print(f"Warning: the {name} AST transformation could not be done.")

    return my_unparse(tree)
