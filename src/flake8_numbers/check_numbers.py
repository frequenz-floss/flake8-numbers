"""A flake8 plugin to check for numbers and their readability."""

import ast
from dataclasses import dataclass
from importlib import metadata
from typing import Any, Iterable, Optional, Tuple, Type


@dataclass
class ErrorReport:
    """A class to represent an error report."""

    line: int
    """The line number of the error."""

    column: int
    """The column number of the error."""

    message: str
    """The error message."""


def _base_value(number_literal: str) -> int:
    """Get the base value of the given number literal.

    Args:
        number_literal: The number literal to get the base value of.

    Returns:
        The base value of the given number literal.
    """
    lower_number_literal = number_literal.lower()
    if lower_number_literal.startswith("0b"):
        return 2
    if lower_number_literal.startswith("0o"):
        return 8
    if lower_number_literal.startswith("0x"):
        return 16
    return 10


def _separator_modulo_for_base(base: int) -> int:
    """Get the separator modulo for the given base.

    Note: We keep this currently as helper function, to make that part of the code
    more readable as well as open up the possibility of making this configurable
    in the future.

    Args:
        base: The base to get the separator modulo for.

    Returns:
        The separator modulo for the given base.
    """
    match base:
        case 2:
            return 4
        case 8:
            return 4
        case 16:
            return 4
        case _:
            return 3


class Flake8NumbersChecker:
    """class to represent a flake8 plugin to check for numbers and their readability."""

    name = "flake8.numbers"
    version = metadata.version("flake8-numbers")
    off_by_default = False

    # Important: The parameter names must match exactly the way how flake8 expects them.
    # This is sadly undocumented and we only found out by looking into the source code.
    # But it is what it is.
    def __init__(self, tree: ast.AST, filename: str) -> None:
        """Initialize the checker.

        Args:
            tree: The AST of the file being checked.
            filename: The path to the file being checked.
        """
        self._tree = tree
        self._filename = filename
        self._source_lines: Optional[list[str]] = None

    @property
    def source_lines(self) -> list[str]:
        """Get the source lines of the file being checked.

        This value is cached on-demand.

        Returns:
            The source lines of the file being checked.
        """
        if self._source_lines is None:
            with open(self._filename, "r", encoding="utf-8") as source_file:
                self._source_lines = source_file.readlines()
        return self._source_lines

    def run(self) -> Iterable[Tuple[int, int, str, Type[Any]]]:
        """Run the checker.

        Yields:
            A tuple of the form (line, column, message, type).
        """
        for node in ast.walk(self._tree):
            if isinstance(node, ast.Constant):
                if result := self.check_constant(node):
                    yield (
                        result.line,
                        result.column,
                        result.message,
                        Flake8NumbersChecker,
                    )

    def _extract_code(self, node: ast.AST) -> str:
        """Extract the code of the given AST node.

        Args:
            node: The AST node to extract the code from.

        Returns:
            The code of the given AST node.
        """
        start_line, start_col = node.lineno, node.col_offset
        end_line, end_col = node.end_lineno, node.end_col_offset
        original_code = "".join(
            line[start_col:end_col].strip()
            for line in self.source_lines[start_line - 1 : end_line]
        )
        return original_code

    def _check_underscore_modulos(
        self,
        fragment: str,
        original_literal: str,
        modulo: int,
        node: ast.Constant,
    ) -> Optional[ErrorReport]:
        """Check the given fragment for underscores at every modulo position.

        Every part of the fragemnt that is separated by an underscore must be of length modulo.
        The first part of the fragment is allowed to be shorter than modulo.

        Args:
            fragment: The fragment to check.
            original_literal: The original literal that the fragment was extracted from.
            modulo: The modulo to check for (e.g. 3 or 4).
            node: The AST node to check.

        Returns:
            An ErrorReport if the fragment is not well formatted.
        """
        parts = fragment.split("_")
        for i, part in enumerate(parts):
            invalid_first_part = i == 0 and len(part) > modulo
            invalid_continuation_part = i != 0 and len(part) != modulo
            if invalid_first_part or invalid_continuation_part:
                message = (
                    f"NUM01: Use underscores every {modulo} digits in large numeric literals"
                    + f" ({original_literal}) for better readability."
                )
                return ErrorReport(
                    line=node.lineno,
                    column=node.col_offset,
                    message=message,
                )

        return None

    def check_constant(self, node: ast.Constant) -> Optional[ErrorReport]:
        """Check for the readability of the given numeric literal.

        Args:
            node: The AST node to check.

        Returns:
            An ErrorReport if the node is a number literal that is not well formatted.
        """
        if type(node.value) not in (int, float):
            return None

        original_literal = self._extract_code(node)

        # NB: We have to check for True and False here, because they are also of type
        #     Constant, but are not numeric literals.
        #     We cannot simply use ast.Num, because that was deprecated.
        if original_literal in ["True", "False"]:
            return None

        base_value = _base_value(original_literal)
        separator_modulo = _separator_modulo_for_base(base_value)
        is_decimal = base_value == 10

        is_science_notation = is_decimal and "e" in original_literal.lower()
        is_float = "." in original_literal

        parts: list[str] = []
        if is_science_notation:
            e_parts: list[str] = original_literal.split("e")
            frac_parts: list[str] = e_parts[0].split(".")
            parts = frac_parts + [e_parts[1]]
        elif is_float:
            parts = original_literal.split(".")
        elif not is_decimal:
            parts = [original_literal[2:]]  # Remove the prefix
        else:
            parts = [original_literal]
            # assert False, "This should never happen"

        for part in parts:
            if error := self._check_underscore_modulos(
                part, original_literal, separator_modulo, node
            ):
                return error

        return None
