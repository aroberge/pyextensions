Modules
========

pyextensions
------------

.. automodule:: pext2
   :members:


unparse
-------

Unparse is a module that is part of the cPython repository,
available under the Tools directory. Because of its location,
it is not available for import by Python programs and has been
copied in the pyextensions repository since we use it for some
AST transformations.

We've added the following function::

    def my_unparse(tree):
        """quick and easy unparsing function"""
        v = io.StringIO()
        Unparser(tree, file=v)
        return v.getvalue()


The original can be found at
https://github.com/python/cpython/blob/master/Tools/parser/unparse.py