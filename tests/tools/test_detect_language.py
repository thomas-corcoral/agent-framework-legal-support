"""Tests for the detect_language tool."""

import pytest

from legal_support.tools.detect_language import (
    SWISS_LANGUAGES,
    LanguageDetectionResult,
    SupportedLanguage,
    detect_language,
    get_preferred_swiss_language,
)


class TestSupportedLanguage:
    """Tests for SupportedLanguage enum."""

    def test_from_code_german(self) -> None:
        """Test converting 'de' code to German."""
        assert SupportedLanguage.from_code("de") == SupportedLanguage.GERMAN
        assert SupportedLanguage.from_code("DE") == SupportedLanguage.GERMAN

    def test_from_code_french(self) -> None:
        """Test converting 'fr' code to French."""
        assert SupportedLanguage.from_code("fr") == SupportedLanguage.FRENCH
        assert SupportedLanguage.from_code("FR") == SupportedLanguage.FRENCH

    def test_from_code_italian(self) -> None:
        """Test converting 'it' code to Italian."""
        assert SupportedLanguage.from_code("it") == SupportedLanguage.ITALIAN
        assert SupportedLanguage.from_code("IT") == SupportedLanguage.ITALIAN

    def test_from_code_english(self) -> None:
        """Test converting 'en' code to English."""
        assert SupportedLanguage.from_code("en") == SupportedLanguage.ENGLISH
        assert SupportedLanguage.from_code("EN") == SupportedLanguage.ENGLISH

    def test_from_code_unknown(self) -> None:
        """Test that unsupported codes return UNKNOWN."""
        assert SupportedLanguage.from_code("es") == SupportedLanguage.UNKNOWN
        assert SupportedLanguage.from_code("zh") == SupportedLanguage.UNKNOWN
        assert SupportedLanguage.from_code("xyz") == SupportedLanguage.UNKNOWN


class TestLanguageDetectionResult:
    """Tests for LanguageDetectionResult model."""

    def test_language_name_german(self) -> None:
        """Test language name for German."""
        result = LanguageDetectionResult(
            language=SupportedLanguage.GERMAN,
            confidence=0.95,
            all_detected={"de": 0.95},
            is_swiss_language=True,
        )
        assert result.language_name == "German (Deutsch)"

    def test_language_name_french(self) -> None:
        """Test language name for French."""
        result = LanguageDetectionResult(
            language=SupportedLanguage.FRENCH,
            confidence=0.90,
            all_detected={"fr": 0.90},
            is_swiss_language=True,
        )
        assert result.language_name == "French (Français)"

    def test_language_name_italian(self) -> None:
        """Test language name for Italian."""
        result = LanguageDetectionResult(
            language=SupportedLanguage.ITALIAN,
            confidence=0.88,
            all_detected={"it": 0.88},
            is_swiss_language=True,
        )
        assert result.language_name == "Italian (Italiano)"

    def test_language_name_english(self) -> None:
        """Test language name for English."""
        result = LanguageDetectionResult(
            language=SupportedLanguage.ENGLISH,
            confidence=0.92,
            all_detected={"en": 0.92},
            is_swiss_language=False,
        )
        assert result.language_name == "English"

    def test_confidence_validation(self) -> None:
        """Test that confidence must be between 0 and 1."""
        with pytest.raises(ValueError):
            LanguageDetectionResult(
                language=SupportedLanguage.GERMAN,
                confidence=1.5,  # Invalid
                all_detected={},
                is_swiss_language=True,
            )


class TestDetectLanguage:
    """Tests for the detect_language function."""

    def test_detect_german(self) -> None:
        """Test detecting German text."""
        text = "Guten Tag, wie geht es Ihnen? Ich habe eine rechtliche Frage."
        result = detect_language(text)
        assert result.language == SupportedLanguage.GERMAN
        assert result.is_swiss_language is True
        assert result.confidence > 0.5

    def test_detect_french(self) -> None:
        """Test detecting French text."""
        text = "Bonjour, comment allez-vous? J'ai une question juridique importante."
        result = detect_language(text)
        assert result.language == SupportedLanguage.FRENCH
        assert result.is_swiss_language is True
        assert result.confidence > 0.5

    def test_detect_italian(self) -> None:
        """Test detecting Italian text."""
        text = "Buongiorno, come sta? Ho una domanda legale molto importante."
        result = detect_language(text)
        assert result.language == SupportedLanguage.ITALIAN
        assert result.is_swiss_language is True
        assert result.confidence > 0.5

    def test_detect_english(self) -> None:
        """Test detecting English text."""
        text = "Hello, how are you? I have an important legal question about Swiss law."
        result = detect_language(text)
        assert result.language == SupportedLanguage.ENGLISH
        assert result.is_swiss_language is False
        assert result.confidence > 0.5

    def test_empty_text_raises_error(self) -> None:
        """Test that empty text raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            detect_language("")

    def test_whitespace_only_raises_error(self) -> None:
        """Test that whitespace-only text raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            detect_language("   ")

    def test_too_short_text_raises_error(self) -> None:
        """Test that very short text raises ValueError."""
        with pytest.raises(ValueError, match="too short"):
            detect_language("ab")

    def test_all_detected_contains_probabilities(self) -> None:
        """Test that all_detected contains language probabilities."""
        text = "Dies ist ein langer deutscher Text mit vielen Wörtern."
        result = detect_language(text)
        assert len(result.all_detected) > 0
        assert all(0.0 <= prob <= 1.0 for prob in result.all_detected.values())


class TestGetPreferredSwissLanguage:
    """Tests for the get_preferred_swiss_language function."""

    def test_swiss_language_returned_directly(self) -> None:
        """Test that Swiss languages are returned directly."""
        german_text = "Das Bundesgericht hat entschieden."
        assert get_preferred_swiss_language(german_text) == SupportedLanguage.GERMAN

    def test_english_falls_back_to_german(self) -> None:
        """Test that English text falls back to German (default)."""
        english_text = "The Federal Court has decided this important case."
        result = get_preferred_swiss_language(english_text)
        # Should fall back to German or find a Swiss language in probabilities
        assert result in SWISS_LANGUAGES


class TestSwissLanguagesConstant:
    """Tests for the SWISS_LANGUAGES constant."""

    def test_swiss_languages_contains_correct_languages(self) -> None:
        """Test that SWISS_LANGUAGES contains the three main Swiss languages."""
        assert SupportedLanguage.GERMAN in SWISS_LANGUAGES
        assert SupportedLanguage.FRENCH in SWISS_LANGUAGES
        assert SupportedLanguage.ITALIAN in SWISS_LANGUAGES

    def test_swiss_languages_excludes_english(self) -> None:
        """Test that SWISS_LANGUAGES does not contain English."""
        assert SupportedLanguage.ENGLISH not in SWISS_LANGUAGES

    def test_swiss_languages_excludes_unknown(self) -> None:
        """Test that SWISS_LANGUAGES does not contain Unknown."""
        assert SupportedLanguage.UNKNOWN not in SWISS_LANGUAGES
