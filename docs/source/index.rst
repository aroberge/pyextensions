.. pyextensions documentation master file, created by
   sphinx-quickstart on Thu Jul 12 10:12:48 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Pyextensions: making it easier to extend Python's syntax
========================================================

To modify Python's syntax, all you need to do is:

1. Get a copy of the CPython's code repository and all the required compilers
   for your platform.
2. Modify the grammar file to add rules for the new syntax.
3. Modify the AST generation code; this requires a knowledge of C
4. Compile the AST into bytecode
5. Recompile the modified Python interpreter

There is a simpler way: it is possible to run code with a modified syntax using import hooks.

    *I think that the majority of Python programmers have no idea that you 
    can even write an import hook at all, let alone how to do it.*

        Steve d'Aprano
        https://mail.python.org/pipermail/python-ideas/2015-May/033633.html

However, not everyone might want to figure out how to write an import hook:

    | [page 420] *...it should be emphasized that Python's module, package and import
      mechanism is one of the most complicated parts of the entire language --
      often poorly understood by even the most seasoned Python programmers
      unless they've devoted effort to peeling back the covers.*
    |     ... long discussion ...
    | [page 428] *Assuming that your head hasn't completely exploded at this point, ...
      Last, but not least, spending some time sleeping with PEP 302 and the
      documentation for* importlib *under your pillow may be advisable.*

        Python Cookbook, 3rd edition, by David Beazley and Brian K. Jones

I believe that standard library should include a (reliable) module that would
facilitate adding syntax changes to Python and run programs with this new
syntax. Pyextensions is a not-so-reliable module that is a proof of concept
for this goal.

Another possibility
-------------------

In addition to using import hooks, it is possible to run code with a modified
syntax by using a specially crafted codec. See for example the `Pyxl project`_.
This is likely not as flexible as the approach we suggest using import hooks.

Quick links to topics
---------------------

.. toctree::
   :maxdepth: 2

    Invocation <invoque>
    Motivation <motivation>
    Contents of various modules <modules>


.. _Pyxl project: https://github.com/dropbox/pyxl

