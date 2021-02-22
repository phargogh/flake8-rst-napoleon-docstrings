import re
import sys
import ast
from typing import Generator, Tuple, Type, Any

from sphinx.ext.napoleon import GoogleDocstring, Config
import rstcheck


if sys.version_info < (3, 8):  # pragma: no cover (<PY38)
    # Third party
    import importlib_metadata
else:  # pragma: no cover (PY38+)
    # Core Library
    import importlib.metadata as importlib_metadata


class Visitor(ast.NodeVisitor):
    def __init__(self):
        self.problems = []

    def visit_FunctionDef(self, node: ast.FunctionDef):
        # clean=True removes all leading spaces far more reliably than
        # textwrap.dedent, not to mention expanding tabs to spaces.
        docstring = ast.get_docstring(node, clean=True)
        if docstring:
            parsed_docstring = GoogleDocstring(docstring).__str__()

            print(parsed_docstring)

            # Line number, column offset, RST error
            for local_line_no, rst_error in rstcheck.check(parsed_docstring):
                self.problems.append(
                    (node.lineno + local_line_no + 1,
                     node.col_offset,
                     "NAP001 " + rst_error))

            # Check documented parameter names against the function signature
            param_names = []
            for param_directive in re.findall(
                    ":param [a-zA-Z0-9_]+:", parsed_docstring):
                # [:-1] trims off the trailing colon
                param_name = re.sub("^:param ", "", param_directive[:-1])
                param_names.append(param_name)

            func_arg_names = {arg.arg: arg for arg in node.args.args}

            # Verify the arguments match (names, order)
            for param_name in param_names:
                if param_name not in func_arg_names:
                    self.problems.append(
                        (node.lineno + 1,  # Report error in docstring
                         node.col_offset,
                         f"NAP002 Arg '{param_name}' not in function signature."
                         ))

            for param_name in func_arg_names:
                if param_name not in param_names:
                    self.problems.append(
                        (node.lineno + 1,  # Report error in docstring
                         node.col_offset,
                         (f"NAP003 Arg {param_name} not described in "
                          "docstring.")))

            # Test that order matches
            if (set(func_arg_names.keys()) == set(param_names) and
                     param_names != [arg.arg for arg in node.args.args]):
                self.problems.append(
                    (node.lineno + 1,  # Report error in docstring
                     node.col_offset,
                     (f"NAP004 Parameter order does not match "
                         "docstring-defined order.")))

        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        # clean=True removes all leading spaces far more reliably than
        # textwrap.dedent, not to mention expanding tabs to spaces.
        docstring = ast.get_docstring(node, clean=True)
        if docstring:
            parsed_docstring = GoogleDocstring(docstring).__str__()

            # Line number, column offset, RST error
            for local_line_no, rst_error in rstcheck.check(parsed_docstring):
                self.problems.append(
                    (node.lineno + local_line_no + 1,
                     node.col_offset,
                     "NAP001 " + rst_error))

        self.generic_visit(node)


class Plugin:
    name = __name__
    version = importlib_metadata.version(__name__)

    def __init__(self, tree: ast.AST) -> None:
        self._tree = tree

    def run(self) -> Generator[Tuple[int, int, str, Type[Any]], None, None]:
        visitor = Visitor()
        visitor.visit(self._tree)

        for line, col, msg in visitor.problems:
            yield line, col, msg, type(self)
