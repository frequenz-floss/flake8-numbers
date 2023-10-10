# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

"""Tests for the flake8_numbers package."""
import ast
import tempfile

from flake8_numbers import check_numbers


def _check_code(code: str) -> list[tuple[int, int, str, type]]:
    """Check code for errors.

    Args:
        code: Code to check.

    Returns:
        List of errors.
    """
    with tempfile.NamedTemporaryFile(mode="w") as file:
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


def _check_okay(code: str) -> None:
    """Check that code is okay.

    Args:
        code: Code to check.
    """
    assert len(_check_code(code)) == 0, f"expected no errors for code '{code}'"


def _check_fail(code: str, count: int = 1) -> None:
    """Check that code is okay.

    Args:
        code: Code to check.
        count: Number of errors expected.
    """
    assert len(_check_code(code)) == count, f"expected {count} errors for code '{code}'"


def test_decimal() -> None:
    """Test that decimal numbers are flagged."""
    _check_okay("1")
    _check_okay("10")
    _check_okay("100")
    _check_okay("1_000")
    _check_okay("10_000")
    _check_okay("100_000")
    _check_okay("-100_000")

    _check_fail("1000")
    _check_fail("10000")
    _check_fail("100_00")


def test_octal() -> None:
    """Test octal numbers, modulo 4 (not 3!)."""
    _check_okay("0o0755")
    _check_okay("0o1740")
    _check_okay("0o1740_1234")
    _check_okay("0o17_1234")
    _check_okay("-0o17_1234")
    _check_fail("0o171_234")


def test_non_integer_constants() -> None:
    """Do not interfere with other constant literal types."""
    _check_okay("True")
    _check_okay("False")
    _check_okay("None")


def test_floating_point_decimal() -> None:
    """
    Test floating point decimal values.

    Require _ modulo 3, also after the decimal point.
    """
    _check_okay("123_456_789.0")
    _check_okay("123_456_789.12")
    _check_okay("123_456_789.12_345")
    _check_okay("123_456_789.123_456_789")
    _check_okay("-123_456_789.123_456_789")
    _check_fail("123_4567_89.123_456_789")
    _check_fail("123_456_789.123456789")
    _check_fail("123_456_789.123456_789")


def test_hexadecimal() -> None:
    """Test hexadecimal values require _ modulo 4."""
    _check_okay("0x1")
    _check_okay("0x12")
    _check_okay("0x123")
    _check_okay("0xDEAD")
    _check_okay("0xDEAD_BEEF")
    _check_okay("0xA_DEAD_BEEF")
    _check_okay("0xAA_DEAD_BEEF")
    _check_okay("0xAAA_DEAD_BEEF")
    _check_okay("-0xAAA_DEAD_BEEF")
    _check_fail("0xDEADBEEF")
    _check_fail("0xAAA_DE_AD_BEEF")
    _check_fail("0xAAA_DEAD_BE_EF")


def test_binary() -> None:
    """Test that binary numbers are flagged."""
    _check_okay("0b1010")
    _check_okay("0b1010_1010")
    _check_okay("0b1010_1010_1010")
    _check_okay("-0b1010_1010_1010")
    _check_fail("0b10101010")
    _check_fail("0b1010_10101010")
