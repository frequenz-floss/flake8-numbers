"""A flake8 plugin to check for numbers and their readability."""

import ast
from dataclasses import dataclass
from typing import Iterable, Optional, Tuple, Type, Any


@dataclass
class ErrorReport:
    """A class to represent an error report."""

    line: int
    column: int
    message: str


class Flake8NumbersChecker:
    """class to represent a flake8 plugin to check for numbers and their readability."""

    name = "flake8-numbers"
    version = "0.1"
    off_by_default = False

    def __init__(self, tree: ast.AST, filepath: str):
        """Initialize the checker.

        Args:
            tree: The AST of the file being checked.
            filepath: The path to the file being checked.
        """
        self._tree = tree
        self._filepath = filepath

    def run(self) -> Iterable[Tuple[int, int, str, Type[Any]]]:
        """Run the checker.

        Yields:
            A tuple of the form (line, column, message, type).
        """
        for node in ast.walk(self._tree):
            if isinstance(node, ast.Constant):
                if isinstance(node.value, (int, float)):
                    if result := self.check_underscores(node):
                        yield (
                            result.line,
                            result.column,
                            result.message,
                            Flake8NumbersChecker,
                        )

    def check_underscores(self, node: ast.Constant) -> Optional[ErrorReport]:
        """Check for the readability of the given numeric literal.

        Args:
            node: The AST node to check.

        Returns:
            An ErrorReport if the node is a number literal that is not well formatted.
        """
        if not isinstance(node.value, (int, float)):
            return

        start_line, start_col = node.lineno, node.col_offset
        end_line, end_col = node.end_lineno, node.end_col_offset
        with open(self._filepath, "r") as f:
            lines = f.readlines()
        original_number = "".join(
            line[start_col:end_col].strip() for line in lines[start_line - 1 : end_line]
        )

        sanitized_number = original_number
        if "." in original_number:
            # Only look at the part before the decimal point
            sanitized_number = original_number[: original_number.index(".")]

        if sanitized_number.startswith("0x"):
            sanitized_number = sanitized_number[2:]

        if "e" in sanitized_number.lower():
            # Skip numbers with scientific notation
            return None

        if "_" in sanitized_number:
            # Skip numbers with underscores
            return None

        if len(sanitized_number.replace(".", "").replace("-", "")) <= 4:
            # Skip small numbers
            return None

        return ErrorReport(
            line=start_line,
            column=start_col,
            message="X101: Use underscores in large numeric literals for better readability",
        )
