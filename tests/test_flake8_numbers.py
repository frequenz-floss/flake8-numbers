# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

"""Tests for the flake8_numbers package."""
import ast
import tempfile

import pytest

from flake8_numbers import check_numbers


def _check_code(code: str) -> list[tuple[int, int, str, type]]:
    """Check code for errors.

    Args:
        code: Code to check.

    Returns:
        List of errors.
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py") as file:
        file_contents = "var = " + code + "\n"
        file.write(file_contents)
        file.flush()
        tree = ast.parse(file_contents, file.name)
        print(f"testing number '{code}' in file '{file.name}'")
        print(f"tree: {tree}")
        checker = check_numbers.Flake8NumbersChecker(tree, file.name)
        result = list(checker.run())
        for error in result:
            print(f"error: {error}")
        print(f"result: {result}")
        return result
        # return list(checker.run())


@pytest.mark.parametrize(
    "expected_errors,code",
    [
        # decimal values require _ modulo 3
        (0, "1"),
        (0, "10"),
        (0, "100"),
        (0, "1_000"),
        (0, "10_000"),
        (0, "100_000"),
        (1, "1000"),
        (1, "10000"),
        (1, "100_00"),
        # floating point decimal values require _ modulo 3, also after the decimal point
        (0, "123_456_789.0"),
        (0, "123_456_789.12"),
        (0, "123_456_789.12_345"),
        (0, "123_456_789.123_456_789"),
        (1, "123_4567_89.123_456_789"),
        (1, "123_456_789.123456789"),
        (1, "123_456_789.123456_789"),
        # hexadecimal values require _ modulo 4
        (0, "0x1"),
        (0, "0x12"),
        (0, "0x123"),
        (0, "0xDEAD"),
        (0, "0xDEAD_BEEF"),
        (0, "0xA_DEAD_BEEF"),
        (0, "0xAA_DEAD_BEEF"),
        (0, "0xAAA_DEAD_BEEF"),
        (1, "0xDEADBEEF"),
        (1, "0xAAA_DE_AD_BEEF"),
        (1, "0xAAA_DEAD_BE_EF"),
    ],
)
def test_large_number_without_underscore(expected_errors: int, code: str) -> None:
    """Test that large numbers without underscores are flagged.

    Args:
        expected_errors: Expected number of errors.
        code: Code to test.
    """
    errors = _check_code(code)
    assert len(errors) == expected_errors
