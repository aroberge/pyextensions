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
prompt = "->> "


class PyextensionsInteractiveConsole(code.InteractiveConsole):
    """A Python console that emulates the normal Python interpreter
       except that it support experimental code transformations."""

    def __init__(self, locals=None, show_python=False):
        self.show_python = show_python
        super().__init__(locals=locals)
        source = transforms.add_all_imports("").split("\n")
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

        source, self.identical = self.do_source_transformations(line)

        try:
            tree = transforms.apply_ast_transformations(source)
            source = _unparse(tree)
        except Exception:
            pass

        source = self.fix_ending(source)

        self._source = source  # in case we need it if we want to show a syntax
        # error - as we reuse the original method rather
        # than rewriting it. See showsyntaxerror() below
        try:
            more = self.runsource(source, self.filename)
        except SystemExit:
            os._exit(1)

        if not more:
            self.resetbuffer()
            if self.show_python and not self.identical:
                self.show_converted(source)
        return more

    def show_converted(self, source):
        """Prints the converted source"""
        print(" ===")
        for line in source.split("\n"):
            print("|", line)
        print(" ===")
        self.identical = True # prevent from showing again

    def showsyntaxerror(self, filename=None):
        """Shows the converted source if different than the original 
           and the syntax error"""
        if not self.identical:
            self.show_converted(self._source)
        super().showsyntaxerror(filename=filename)

    def do_source_transformations(self, line):
        """Performs the source transformations on the current content.

           Returns the transformed source and a flag indicating if
           the transformed source is different from the original source
        """
        # Source transformation may raise an exception
        # if a statement ends with a colon, not knowing how to deal with
        # To cure this problem, we temporarily add a pass keyword to
        # complete such block, removing it after the transformation has

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
        return source, identical

    def fix_ending(self, source):
        """Ensures that the last blank lines of the transformed source are consistent
        with what was provided by the user."""

        # Some transformations may add or strip an empty line meant to
        # end a block, or strip non-empty lines (but with spaces) at the end
        # mean to continue a block, etc.
        # We ensure that the transformed source has the same combination
        # of white spaces and \n characters at the end as the original

        last_lines = reversed(self.buffer)
        blank_lines = []
        for line in last_lines:
            if not line.strip():
                blank_lines.append(line)
            else:
                break

        blank_lines = reversed(blank_lines)
        lines = source.rstrip().split("\n")
        lines.extend(blank_lines)
        source = "\n".join(lines)
        return source


def import_transformer(name):
    mod = transforms.import_transformer(name)
    if hasattr(mod, "export_to_console"):
        for key in mod.export_to_console:
            setattr(builtins, key, mod.export_to_console[key])
    return mod


def start_console(local_vars=None, show_python=False):
    """Starts a console; modified from code.interact"""
    console_defaults = {"import_transformer": import_transformer}

    if local_vars is None:
        local_vars = console_defaults
    else:
        local_vars.update(console_defaults)

    sys.ps1 = prompt
    console = PyextensionsInteractiveConsole(locals=local_vars, show_python=show_python)
    console.locals.update(console_defaults)
    console.interact(banner=banner)
