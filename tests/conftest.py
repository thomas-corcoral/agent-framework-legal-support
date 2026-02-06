"""Pytest configuration and fixtures for Swiss Federal Court Data Generation tests."""

from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def test_data_dir(project_root: Path) -> Path:
    """Return the test data directory."""
    data_dir = project_root / "tests" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


@pytest.fixture(scope="session")
def sample_court_decision() -> dict:
    """Return a sample court decision for testing."""
    return {
        "docref": "1C_123/2024",
        "text": "Dies ist ein Beispiel-Bundesgerichtsentscheid...",
        "division": "I. öffentlich-rechtliche Abteilung",
        "division_type": "Beschwerde",
        "area_general": "Öffentliches Recht",
        "area_intermediate": "Verwaltungsrecht",
        "area_detailed": "Baurecht",
        "topic": "Baubewilligung",
        "issue": "Anfechtung einer Baubewilligung",
        "source_canton": "ZH",
        "outcome": "Abweisung",
        "cited_bger": "1C_100/2023;1C_50/2022",
        "cited_bge": "140 II 25;138 I 143",
    }


@pytest.fixture
def mock_env_vars(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """Set up mock environment variables for testing."""
    test_vars = {
        "OPENAI_API_KEY": "sk-test-key-12345",
        "ANTHROPIC_API_KEY": "sk-ant-test-key",
        "GOOGLE_API_KEY": "test-google-key",
        "LOG_LEVEL": "DEBUG",
        "MAX_WORKERS": "2",
        "BATCH_SIZE": "10",
    }

    for key, value in test_vars.items():
        monkeypatch.setenv(key, value)

    yield

    # Cleanup happens automatically via monkeypatch


@pytest.fixture(scope="session")
def output_dir(project_root: Path) -> Path:
    """Return the output directory for test results."""
    out_dir = project_root / "tests" / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir
