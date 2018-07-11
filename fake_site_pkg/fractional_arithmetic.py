"""Converts integers literals into instances of the Fraction"""
import ast
from fractions import Fraction

class FractionWrapper(ast.NodeTransformer):
    """Wraps all integers in a call to Integer()"""
    def visit_Num(self, node):
        if isinstance(node.n, int):
            return ast.Call(func=ast.Name(id='Fraction', ctx=ast.Load()),
                            args=[node], keywords=[])
        return node

def transform_ast(tree):
    tree1 = ast.parse("from fractions import Fraction")
    tree = FractionWrapper().visit(tree)
    tree1.body += tree.body
    # Add lineno & col_offset to the nodes we created
    ast.fix_missing_locations(tree1)
    return tree1
