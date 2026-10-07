"""Is a saved text file only a change of words?

    python3 build/texts_check.py OLD_FILE < NEW_TEXT

The editing page runs this before it saves one of the text files (content.py, content_pages.py, strings_es.py).
Both versions are parsed. Every string, number, list or dict of plain values, and every call of the file's own small
helpers (dict, P) with plain values, is blanked. What remains, the shape of the code, must be the same. So words can
change and entries can be added to a list or a dict, but nothing that would run as code can be added: no import, no
other call, no function, no changed expression. A person with the editing password can
change what the site says, and nothing more.

Exit 0: only words changed. Exit 1: the new text is not valid Python (the message says where). Exit 2: it adds or changes code.
"""
import ast
import sys


def helpers(tree):
    """The names a text file may call with plain values: dict, and the small helpers the file itself defines
    (content.py has P = lambda ...: dict(...) for its photos, and a def or two). Their bodies are part of the shape
    that must not change, so calling them with new words is as safe as writing a dict."""
    names = {"dict"}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            names.add(node.name)
        elif isinstance(node, ast.Assign) and isinstance(node.value, ast.Lambda):
            names.update(t.id for t in node.targets if isinstance(t, ast.Name))
    return names


def plain(node, names):
    """Only words and numbers, in lists, tuples, sets and dicts, or passed to one of the helpers."""
    if isinstance(node, ast.Constant):
        return True
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return all(plain(e, names) for e in node.elts)
    if isinstance(node, ast.Dict):
        return all(k is not None and plain(k, names) for k in node.keys) and all(plain(v, names) for v in node.values)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        return plain(node.operand, names)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in names:
        return (all(plain(a, names) for a in node.args)
                and all(k.arg is not None and plain(k.value, names) for k in node.keywords))
    return False


class Blank(ast.NodeTransformer):
    """Words become one blank. A list, dict or helper call made only of words becomes one blank too, whatever its length.
    Everything else, the shape of the code, stays and must match."""
    def __init__(self, names):
        self.names = names

    def collapse(self, node):
        if plain(node, self.names):
            return ast.Constant(value=None)
        return self.generic_visit(node)

    visit_Constant = visit_List = visit_Tuple = visit_Set = visit_Dict = visit_Call = visit_UnaryOp = collapse


def shape(source, names):
    tree = ast.parse(source)
    tree = Blank(names).visit(tree)
    return ast.dump(tree, include_attributes=False)


def main():
    old = open(sys.argv[1], encoding="utf-8").read()
    new = sys.stdin.read()
    names = helpers(ast.parse(old))          # the helpers of the OLD file: a new one cannot be smuggled in with its call
    try:
        new_shape = shape(new, names)
    except SyntaxError as e:
        print("line %s: %s" % (e.lineno, e.msg))
        sys.exit(1)
    if shape(old, names) != new_shape:
        print("this save changes the code of the file, not only its words")
        sys.exit(2)
    print("only words changed")


if __name__ == "__main__":
    main()
