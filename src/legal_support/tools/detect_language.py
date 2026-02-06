"""Language detection tool for Swiss Legal Support.

This module provides language detection functionality using the langdetect library,
specifically tailored for Swiss national languages (German, French, Italian) and English.
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated

from langdetect import LangDetectException, detect, detect_langs
from pydantic import BaseModel, Field


class SupportedLanguage(str, Enum):
    """Supported languages for Swiss Legal Support.

    Switzerland has four national languages. We support the three main ones
    plus English for international users.
    """

    GERMAN = "de"
    FRENCH = "fr"
    ITALIAN = "it"
    ENGLISH = "en"
    UNKNOWN = "unknown"

    @classmethod
    def from_code(cls, code: str) -> SupportedLanguage:
        """Convert a language code to SupportedLanguage enum.

        Args:
            code: ISO 639-1 language code (e.g., 'de', 'fr', 'it', 'en')

        Returns:
            The corresponding SupportedLanguage enum value, or UNKNOWN if not supported.
        """
        code_lower = code.lower()
        for lang in cls:
            if lang.value == code_lower:
                return lang
        return cls.UNKNOWN


class LanguageDetectionResult(BaseModel):
    """Result of language detection.

    Attributes:
        language: The detected primary language.
        confidence: Confidence score for the detection (0.0 to 1.0).
        all_detected: All detected languages with their probabilities.
        is_swiss_language: Whether the detected language is a Swiss national language.
    """

    language: SupportedLanguage = Field(description="The detected primary language")
    confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence score for the detection (0.0 to 1.0)"
    )
    all_detected: dict[str, float] = Field(
        default_factory=dict, description="All detected languages with their probabilities"
    )
    is_swiss_language: bool = Field(
        description="Whether the detected language is a Swiss national language"
    )

    @property
    def language_name(self) -> str:
        """Get the human-readable name of the detected language."""
        names = {
            SupportedLanguage.GERMAN: "German (Deutsch)",
            SupportedLanguage.FRENCH: "French (Français)",
            SupportedLanguage.ITALIAN: "Italian (Italiano)",
            SupportedLanguage.ENGLISH: "English",
            SupportedLanguage.UNKNOWN: "Unknown",
        }
        return names.get(self.language, "Unknown")


SWISS_LANGUAGES = {SupportedLanguage.GERMAN, SupportedLanguage.FRENCH, SupportedLanguage.ITALIAN}


def detect_language(
    text: Annotated[str, Field(description="The text to detect the language of")],
) -> LanguageDetectionResult:
    """Detect the language of the given text.

    This function uses the langdetect library to identify the language of the input text.
    It specifically handles Swiss national languages (German, French, Italian) and English.

    Args:
        text: The text to detect the language of. Should be at least a few words
              for accurate detection.

    Returns:
        LanguageDetectionResult containing the detected language, confidence score,
        all detected language probabilities, and whether it's a Swiss language.

    Raises:
        ValueError: If the text is empty or too short for detection.

    Examples:
        >>> result = detect_language("Guten Tag, wie geht es Ihnen?")
        >>> result.language
        <SupportedLanguage.GERMAN: 'de'>
        >>> result.is_swiss_language
        True

        >>> result = detect_language("Bonjour, comment allez-vous?")
        >>> result.language
        <SupportedLanguage.FRENCH: 'fr'>

        >>> result = detect_language("Buongiorno, come sta?")
        >>> result.language
        <SupportedLanguage.ITALIAN: 'it'>
    """
    if not text or not text.strip():
        raise ValueError("Text cannot be empty for language detection")

    text = text.strip()

    if len(text) < 3:
        raise ValueError("Text is too short for accurate language detection (minimum 3 characters)")

    try:
        detected_code = detect(text)
        detected_probs = detect_langs(text)

        all_detected = {str(lang.lang): lang.prob for lang in detected_probs}

        language = SupportedLanguage.from_code(detected_code)

        confidence = all_detected.get(detected_code, 0.0)

        is_swiss = language in SWISS_LANGUAGES

        return LanguageDetectionResult(
            language=language,
            confidence=confidence,
            all_detected=all_detected,
            is_swiss_language=is_swiss,
        )

    except LangDetectException:
        return LanguageDetectionResult(
            language=SupportedLanguage.UNKNOWN,
            confidence=0.0,
            all_detected={},
            is_swiss_language=False,
        )


def get_preferred_swiss_language(
    text: Annotated[str, Field(description="The text to analyze")],
) -> SupportedLanguage:
    """Get the preferred Swiss language from the text.

    If the detected language is not a Swiss national language, this function
    attempts to find the most likely Swiss language from the detection results.

    Args:
        text: The text to analyze.

    Returns:
        The preferred Swiss language (German, French, or Italian).
        Defaults to German if no Swiss language can be determined.

    Examples:
        >>> get_preferred_swiss_language("Hello, I need help")
        <SupportedLanguage.GERMAN: 'de'>  # Falls back to German
    """
    result = detect_language(text)

    if result.is_swiss_language:
        return result.language

    swiss_probs = {
        lang: prob
        for lang, prob in result.all_detected.items()
        if SupportedLanguage.from_code(lang) in SWISS_LANGUAGES
    }

    if swiss_probs:
        best_swiss = max(swiss_probs, key=swiss_probs.get)  # type: ignore[arg-type]
        return SupportedLanguage.from_code(best_swiss)

    return SupportedLanguage.GERMAN
