"""pyextensions is a proof-of-concept of implementing code transformations
using import hooks. I believe that a module like pyextensions would be
a nice addition to Python's standard library.

By code transformation, we mean that instead of executing the code found
in a module *as is*, it is first transformed prior to its execution.
The transformations are done by other modules, called transformers, which
are normal Python file.

A transformer needs to include at least one of the following:

1. a function named ``transform_source()`` which takes as its argument a string,
   like the content of a regular Python script, modifies it, and return another
   string.  Such transformations can be chained.
2. a function named ``transform_ast()`` which takes as its argument an abstract
   syntax tree, modifies it, and returns another tree. Such transformations can
   also be chained.

Ideally, a third type of transformations, identified by a function named
``transform_bytecode()``, should be allowed; however, we have not been able
so far to implement this.

In addition to the above, we have found that some transformations would require
that the module to be transformed and executed should also import some
additional modules.  While this could be done using the ``transform_source()``
function to simply prepend the required imports in the transformed source,
we have found it useful to do this using another function named ``add_import``.

Modules to be transformed should not have a ".py" extension. By default,
this module looks for files ending with a ".notpy" extension; however, this
can be changed as described below.
"""
import argparse
import ast
import os.path
import sys

from importlib import import_module
from importlib.abc import Loader, MetaPathFinder
from importlib.util import spec_from_file_location


def create_fake_site_packages_dir():
    """It is assumed that code transformers are third-party modules
    to be installed in a location from where they can be imported.
    For this proof of concept, we add a fake site-packages directory
    where the sample transformers will be located.
    """
    top_dir = os.path.abspath(os.path.dirname(__file__))
    fake_site_pkg = os.path.join(top_dir, "fake_site_pkg")

    if not os.path.exists(fake_site_pkg):
        raise NotImplementedError(
            "A fake_site_pkg directory must exist for this demo to work correctly."
        )
    sys.path.insert(0, fake_site_pkg)


create_fake_site_packages_dir()

# The import hook utility provided by pyextensions can be used in
# interactive mode, given a specifically crafted REPL.
# Through experimentation, we have found that transformers need to behave
# slightly differently depending on the context and thus need to be aware
# of the context in which they are called.
# CONFIG["interactive"] plays that role as a global variable,
# accessible both to the REPL and the various transformers.
CONFIG = {
    "interactive": False,  # Not used explicitly in this module.
    "file_ext": "notpy",
    "main_module_name": None,
    "version": 0.2,
}
TRANSFORMERS = {"<cache>": []}  # [(tr_name1, tr_mod1), ...]


class ExtensionMetaFinder(MetaPathFinder):
    """A custom finder to locate modules, based on looking for files
       with a specific extension."""

    def find_spec(self, fullname, path, target=None):
        """Finds the appropriate properties (spec) of a module, and sets
           its loader."""
        if not path:
            path = [os.getcwd()]
        if "." in fullname:
            module_name = fullname.split(".")[-1]
        else:
            module_name = fullname
        for entry in path:
            if os.path.isdir(os.path.join(entry, module_name)):
                # this module has child modules
                filename = os.path.join(entry, module_name, "__init__.py")
                submodule_locations = [os.path.join(entry, module_name)]
            else:
                filename = os.path.join(entry, module_name + "." + CONFIG["file_ext"])
                submodule_locations = None

            if not os.path.exists(filename):
                continue

            return spec_from_file_location(
                fullname,
                filename,
                loader=ExtensionLoader(filename),
                submodule_search_locations=submodule_locations,
            )
        return None  # we don't know how to import this; default to others


sys.meta_path.insert(0, ExtensionMetaFinder())


class ExtensionLoader(Loader):
    """A custom loader which transforms the source prior to its execution"""

    def __init__(self, filename):
        self.filename = filename

    def exec_module(self, module):
        """Import the source code, transforms it before executing it so that
           it becomes valid Python."""
        if not (
            self.filename.endswith(CONFIG["file_ext"])
            or self.filename.endswith("__init__.py")  # noqa
        ):
            print("Fatal error: ExtensionLoader is asked to load a normal file.")
            print("filename:", self.filename)
            print("Expected extension:", CONFIG["file_ext"])
            raise SystemExit

        module_name = module.__name__
        if module.__name__ == CONFIG["main_module_name"]:
            module.__name__ = "__main__"

        with open(self.filename) as f:
            source = f.read()

        get_required_transformers(module_name, source)

        if TRANSFORMERS[module_name]:
            source = apply_source_transformations(source)
            tree = ast.parse(source)
            tree = apply_ast_transformations(tree)
            co = compile(tree, module_name, "exec")
            exec(co, vars(module))


def import_main(module_name):
    """Imports the module that is to be interpreted as the main module.

       pyextensions would normally be called with a script meant to be run as
       the main module with its source to be transformed.
       This script is specified the -s (or --source) option, as in::

           python -m pyextensions -s name

       With the -m flag, Python identifies pyextensions as the main script;
       we artificially change this so that "main_script" is properly
       identified as ``name``.
    """
    CONFIG["main_module_name"] = module_name
    return import_module(module_name)


def get_required_transformers(module_name, source):
    """
    Scan a source for lines of the form::

        #ext transformer1 [transformer2 ...]

    identifying transformers to be used and ensure that they are imported
    in the order in which they are specifid in the file.
    """
    lines = source.split("\n")
    for number, line in enumerate(lines):
        if line.startswith("#ext "):
            line = line[5:]
            for trans_name in line.split(" "):
                import_transformer(module_name, trans_name.strip())
    return None


def import_transformer(module_name, trans_name):
    """This function needed, import a transformer for a given module and
       appends it to the appropriate lists.

       The code inside a module where a transformer is defined should be
       standard Python code, which does not need any transformation.
       So, we disable the import hook, and let the normal module import
       do its job - which is faster and likely more reliable than our
       custom method.
    """
    if module_name in TRANSFORMERS:
        for (name, transformer) in TRANSFORMERS[module_name]:
            if name == trans_name:
                return transformer
    else:
        for (name, transformer) in TRANSFORMERS["<cache>"]:
            if name == trans_name:
                if module_name not in TRANSFORMERS:
                    TRANSFORMERS[module_name] = []
                TRANSFORMERS[module_name].append((name, transformer))
                return transformer

    # We have not imported the required transformer before.

    hook = sys.meta_path[0]
    sys.meta_path = sys.meta_path[1:]
    try:
        transformer = __import__(trans_name)
    except ImportError:
        sys.stderr.write(
            "Fatal: Import Error in add_transformers: %s not found\n" % trans_name
        )
        raise SystemExit
    except Exception as e:
        sys.stderr.write(
            "\nUnexpected exception in import_transformer %s\n " % e.__class__.__name__
        )
        sys.stderr.write(str(e.args))
        sys.stderr.write(f"\nname = {trans_name}\n")

    sys.meta_path.insert(0, hook)  # restore import hook

    TRANSFORMERS["<cache>"].append((trans_name, transformer))
    if module_name not in TRANSFORMERS:
        TRANSFORMERS[module_name] = []
    TRANSFORMERS[module_name].append((trans_name, transformer))

    return transformer


##############
# The code above dealt with adding an import hook, identifying and loading
# transformers and redefining a __main__ module.
#
# What follows is the code required for doing the actual transformations.
############

def apply_source_transformations(module_name, source):
    """Used to convert the source code, applying all the transformers
       specified in the module, in the order specified.

       Source transformers are transformers that contain a function named
       ``transform_source``.
    """
    if module_name not in TRANSFORMERS:
        return source

    for trans_name, transformer in TRANSFORMERS[module_name]:
        if hasattr(transformer, "transform_source"):
            source = transformer.transform_source(source)
    return source


def apply_ast_transformations(module_name, tree):
    """Used to convert the code by applying AST transformations,
       applying all the transformers specified in the module,
       in the order specified.

       AST transformers are applied on a abstract syntax tree.
       They are transformers that contain a function named
       ``transform_ast`` which take and abstract syntax tree as input
       and return a new tree.
    """
    if module_name not in TRANSFORMERS:
        return tree

    for trans_name, transformer in TRANSFORMERS[module_name]:
        if hasattr(transformer, "transform_ast"):
            tree = transformer.transform_ast(tree)
    return tree


def main():
    """**Basic invocation**

    The primary role of pyextensions is to run programs that have a modified syntax.
    This is done by one of the following alternatives::

        python -m pyextensions -s path/to/name
        python pyextensions.py -s path/to/name
        or ...  --source path/to/name

    where ``name`` refers to a file named ``name.notpy``. Any subsequent
    ``import`` statement will first look for file whose extension is ``notpy``
    before looking for normal ``py`` or ``pyc`` files.
    Any file with the ``notpy`` extension that is imported will also be
    processed by the relevant source transformers.
    Normal Python files will bypass the transformations.

    A different extension that ``notpy`` can be specified as follows::

        python -m pyextensions -s name -x EXTENSION
        or --file_extension EXTENSION
    """
    parser = argparse.ArgumentParser(
        description="""
        pyextensions sets up an import hook which
        makes it possible to run a file that contains modified Python syntax
        provided the relevant source transformers can be imported.
        """
    )
    parser.add_argument(
        "-s",
        "--source",
        help="""Source file to be transformed.
                Format: path.to.file -- Do not include an extension.""",
    )
    parser.add_argument(
        "-x",
        "--file_extension",
        help="The file extension of the module to load; default=notpy",
    )

    parser.add_argument(
        "-c",
        "--convert",
        help="Show the original code and the code transformed into standard Python.",
        action="store_true",
    )

    args = parser.parse_args()

    if args.file_extension is not None:
        CONFIG["file_ext"] = args.file_extension

    if args.source is not None:
        try:
            CONFIG["main_module"] = import_main(args.source)
        except ModuleNotFoundError:
            print("Could not find module ", args.source, "\n")
            raise
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
