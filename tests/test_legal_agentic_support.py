"""Tests for swiss_court_data_gen.synthetic_data_generation module."""

from __future__ import annotations

from io import StringIO
from unittest.mock import patch

from legal_support import __version__, legal_support
from legal_support.legal_agentic_support import main


def test_main_runs_without_error() -> None:
    """Test that main() runs without raising exceptions."""
    # Should not raise any exception
    main()


def test_main_prints_version() -> None:
    """Test that main() prints the version."""
    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
        main()
        output = mock_stdout.getvalue()

    assert __version__ in output
    assert "Swiss Court Data Generation" in output


def test_main_prints_hello_world() -> None:
    """Test that main() prints Hello World."""
    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
        main()
        output = mock_stdout.getvalue()

    assert "Hello World!" in output


def test_main_prints_coming_soon() -> None:
    """Test that main() indicates implementation is coming soon."""
    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
        main()
        output = mock_stdout.getvalue()

    assert "Synthetic data generation implementation coming soon" in output


def test_module_can_be_imported() -> None:
    """Test that the synthetic_data_generation module can be imported."""
    assert legal_support is not None


def test_main_function_exists() -> None:
    """Test that main function is defined in synthetic_data_generation module."""
    assert callable(main)


def test_main_returns_none() -> None:
    """Test that main() returns None."""
    result = main()
    assert result is None


def test_main_output_line_count() -> None:
    """Test that main() produces expected number of output lines."""
    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
        main()
        output = mock_stdout.getvalue()

    lines = [line for line in output.strip().split("\n") if line]
    assert len(lines) == 3, f"Expected 3 output lines, got {len(lines)}"


def test_main_version_line_format() -> None:
    """Test that the version line has expected format."""
    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
        main()
        output = mock_stdout.getvalue()

    lines = output.strip().split("\n")
    version_line = lines[0]
    assert f"v{__version__}" in version_line


def test_module_docstring_exists() -> None:
    """Test that the module has a docstring."""
    assert legal_support.__doc__ is not None
    assert len(legal_support.__doc__) > 0


def test_main_docstring_exists() -> None:
    """Test that main function has a docstring."""
    assert main.__doc__ is not None
    assert len(main.__doc__) > 0
