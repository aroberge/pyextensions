import ast
import builtins
import io
import code
import platform
import os
import sys

from . import transforms
from . import version
from . import unparse

def _unparse(tree):
    v = io.StringIO()
    unparse.Unparser(tree, file=v)
    return v.getvalue()


# define banner and prompt here so that they can be imported in tests
banner = "pyextensions console version {}. [Python version: {}]\n".format(
    version.__version__, platform.python_version()
)
prompt ="->> "


class PyextensionsInteractiveConsole(code.InteractiveConsole):
    """A Python console that emulates the normal Python interpreter
       except that it support experimental code transformations."""

    def __init__(self, locals=None, show_python=False):
        self.show_python = show_python
        super().__init__(locals=locals)
        source = transforms.add_all_imports('').split("\n")
        for line in source:
            self.push(line)

    def push(self, line):
        """Transform and push a line to the interpreter.

        The line should not have a trailing newline; it may have
        internal newlines.  The line is appended to a buffer and the
        interpreter's runsource() method is called with the
        concatenated contents of the buffer as source.  If this
        indicates that the command was executed or invalid, the buffer
        is reset; otherwise, the command is incomplete, and the buffer
        is left as it was after the line was appended.  The return
        value is 1 if more input is required, 0 if the line was dealt
        with in some way (this is the same as runsource()).

        """
        self.buffer.append(line)

        # Source transformation using the tokenize module occasionally mess
        # up if a statement ends with a colon. To cure this problem,
        # we temporarily add a pass keyword to complete the block,
        # removing it after the transformation has

        add_pass = False
        if line.rstrip(" ").endswith(":"):
            add_pass = True
        source = "\n".join(self.buffer)
        if add_pass:
            source += "pass"

        identical = True
        newsource = transforms.apply_source_transformations(source)
        if newsource != source:
            identical = False

        source = newsource
        if add_pass:
            source = source.rstrip(" ")
            if source.endswith("pass"):
                source = source[:-4]

        try:
            tree = transforms.apply_ast_transformations(source)
            source = _unparse(tree)
        except Exception:
            pass

        # Some transformations may add or strip an empty line meant to 
        # end a block. We ensure that the source to be compiled has
        # the same ending as the code entered
        if self.buffer[-1].strip():
            source = source.rstrip()
        else:
            source += "\n"  # might now always be needed

        try:
            more = self.runsource(source, self.filename)
        except SystemExit:
            os._exit(1)

        if not more:
            self.resetbuffer()
            if self.show_python and not identical:
                for line in source.split("\n"):
                    print("#", line)
        return more


def import_transformer(name):
    mod = transforms.import_transformer(name)
    if hasattr(mod, 'export_to_console'):
        for key in mod.export_to_console:
            setattr(builtins, key, mod.export_to_console[key]) 
    return mod


def start_console(local_vars=None, show_python=False):
    """Starts a console; modified from code.interact"""
    console_defaults = {
        "import_transformer": import_transformer
    }

    if local_vars is None:
        local_vars = console_defaults
    else:
        local_vars.update(console_defaults)

    sys.ps1 = prompt
    console = PyextensionsInteractiveConsole(locals=local_vars, show_python=show_python)
    console.locals.update(console_defaults)
    console.interact(banner=banner)
