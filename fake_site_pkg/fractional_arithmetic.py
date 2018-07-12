"""Converts integers literals into instances of the Fraction"""
import ast

def add_import():
    return "from fractions import Fraction\n"

class FractionWrapper(ast.NodeTransformer):
    """Wraps all integers in a call to Integer()"""
    def visit_Num(self, node):
        if isinstance(node.n, int):
            return ast.Call(func=ast.Name(id='Fraction', ctx=ast.Load()),
                            args=[node], keywords=[])
        return node

def transform_ast(tree):
    import sys
    tree = FractionWrapper().visit(tree)
    ast.fix_missing_locations(tree)
    return tree

