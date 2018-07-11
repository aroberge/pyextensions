import ast
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

        add_pass = False
        if line.rstrip(" ").endswith(":"):
            add_pass = True
        source = "\n".join(self.buffer)
        if add_pass:
            source += "pass"

        _transformed = False
        newsource = transforms.apply_source_transformations(source)
        if newsource != source:
            _transformed = True

        source = newsource
        if add_pass:
            source = source.rstrip(" ")
            if source.endswith("pass"):
                source = source[:-4]

        # some transformations may strip an empty line meant to end a block
        if not self.buffer[-1]:
            source += "\n"

        try:
            tree = transforms.apply_ast_transformations(source)
            source = _unparse(tree)
        except Exception:
            pass

        try:
            more = self.runsource(source, self.filename)
        except SystemExit:
            os._exit(1)

        if not more:
            self.resetbuffer()
            if self.show_python and _transformed:
                for line in source.split("\n"):
                    print("#", line)
        return more


console_defaults = {"import_transformer": transforms.import_transformer}


def start_console(local_vars=None, show_python=False):
    """Starts a console; modified from code.interact"""
    if local_vars is None:
        local_vars = console_default
    else:
        local_vars.update(console_defaults)
    sys.ps1 = prompt
    console = PyextensionsInteractiveConsole(locals=local_vars, show_python=show_python)
    console.interact(banner=banner)
