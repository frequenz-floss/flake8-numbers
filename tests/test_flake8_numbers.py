# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

"""Tests for the flake8_numbers package."""
import pytest
import pytest_flake8_path


@pytest.mark.parametrize(
    "code,expected_errors",
    [
        # decimal values require _ modulo 3
        ("v = 10000\n", 1),
        ("v = 100_00\n", 1),
        ("v = 100_000\n", 0),
        # floating point decimal values require _ modulo 3, also after the decimal point
        ("v = 123_456_789.123_456_789\n", 1),
        ("v = 123_456_789.123456789\n", 1),
        ("v = 123_456_789.0\n", 0),
        # hexadecimal values require _ modulo 4
        ("v = 0xDEADBEEF\n", 1),
        ("v = 0xDEAD_BEEF\n", 0),
    ],
)
def test_large_number_without_underscore(
    code: str,
    expected_errors: int,
    flake8_path: pytest_flake8_path.Flake8Path,
):
    """Test that large numbers without underscores are flagged.

    Args:
        code: Code to test.
        expected_errors: Expected number of errors.
        flake8_path: fixture to test flake8 plugins.
    """
    flake8_path.write_text(code)
    result = flake8_path.run_flake8()
    assert len(result.out_lines) == expected_errors
