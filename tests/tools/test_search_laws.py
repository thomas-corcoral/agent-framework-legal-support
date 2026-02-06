"""Tests for the search_laws tool."""

from __future__ import annotations

import pytest

from legal_support.tools.search_laws import (
    FedlexAPIError,
    Language,
    LawArticle,
    LawEntry,
    LawSearchResult,
    LawType,
    LegalDomain,
    get_common_law_abbreviations,
    get_law_by_sr_number,
    search_laws,
)


class TestLegalDomain:
    """Tests for LegalDomain enum."""

    def test_all_domains_have_values(self) -> None:
        """All legal domains should have string values."""
        assert LegalDomain.CONSTITUTION.value == "1"
        assert LegalDomain.PRIVATE_LAW.value == "2"
        assert LegalDomain.CRIMINAL_LAW.value == "3"
        assert LegalDomain.ALL.value == "all"

    def test_domain_count(self) -> None:
        """Should have 11 legal domains including ALL."""
        assert len(LegalDomain) == 11


class TestLawType:
    """Tests for LawType enum."""

    def test_law_types(self) -> None:
        """Should have correct law type values."""
        assert LawType.FEDERAL_ACT.value == "federal_act"
        assert LawType.ORDINANCE.value == "ordinance"
        assert LawType.CONSTITUTION.value == "constitution"
        assert LawType.ALL.value == "all"


class TestLanguage:
    """Tests for Language enum."""

    def test_language_codes(self) -> None:
        """Should have correct ISO language codes."""
        assert Language.GERMAN.value == "de"
        assert Language.FRENCH.value == "fr"
        assert Language.ITALIAN.value == "it"
        assert Language.ROMANSH.value == "rm"
        assert Language.ENGLISH.value == "en"


class TestLawArticle:
    """Tests for LawArticle model."""

    def test_create_article(self) -> None:
        """Should create a valid law article."""
        article = LawArticle(
            article_number="Art. 8",
            title="Equality",
            content="All persons are equal before the law.",
            paragraph="1",
        )
        assert article.article_number == "Art. 8"
        assert article.title == "Equality"
        assert article.content == "All persons are equal before the law."
        assert article.paragraph == "1"

    def test_article_optional_fields(self) -> None:
        """Optional fields should default to None."""
        article = LawArticle(
            article_number="Art. 1",
            content="Some content",
        )
        assert article.title is None
        assert article.paragraph is None


class TestLawEntry:
    """Tests for LawEntry model."""

    def test_create_entry(self) -> None:
        """Should create a valid law entry."""
        entry = LawEntry(
            sr_number="220",
            title="Obligationenrecht",
            abbreviation="OR",
            law_type="Federal Act",
            language=Language.GERMAN,
            fedlex_url="https://www.fedlex.admin.ch/eli/cc/220/de",
        )
        assert entry.sr_number == "220"
        assert entry.abbreviation == "OR"
        assert entry.full_citation == "OR (SR 220)"

    def test_full_citation_without_abbreviation(self) -> None:
        """Full citation should work without abbreviation."""
        entry = LawEntry(
            sr_number="999.1",
            title="Some Law",
            abbreviation=None,
            law_type="Federal Act",
            language=Language.GERMAN,
            fedlex_url="https://www.fedlex.admin.ch/eli/cc/999.1/de",
        )
        assert entry.full_citation == "SR 999.1"

    def test_entry_optional_fields(self) -> None:
        """Optional fields should have correct defaults."""
        entry = LawEntry(
            sr_number="100",
            title="Test Law",
            law_type="Federal Act",
            language=Language.GERMAN,
            fedlex_url="https://example.com",
        )
        assert entry.abbreviation is None
        assert entry.enactment_date is None
        assert entry.entry_into_force is None
        assert entry.relevant_articles == []
        assert entry.summary is None


class TestLawSearchResult:
    """Tests for LawSearchResult model."""

    def test_create_result(self) -> None:
        """Should create a valid search result."""
        result = LawSearchResult(
            query="test",
            domain=LegalDomain.ALL,
            language=Language.GERMAN,
            total_results=0,
            results=[],
            search_timestamp="2024-01-01T00:00:00Z",
        )
        assert result.query == "test"
        assert result.total_results == 0
        assert result.results == []

    def test_result_with_entries(self) -> None:
        """Should handle results with law entries."""
        entry = LawEntry(
            sr_number="220",
            title="OR",
            law_type="Federal Act",
            language=Language.GERMAN,
            fedlex_url="https://example.com",
        )
        result = LawSearchResult(
            query="contract",
            domain=LegalDomain.PRIVATE_LAW,
            language=Language.GERMAN,
            total_results=1,
            results=[entry],
            search_timestamp="2024-01-01T00:00:00Z",
        )
        assert result.total_results == 1
        assert len(result.results) == 1


class TestSearchLaws:
    """Tests for search_laws function."""

    def test_search_by_abbreviation(self) -> None:
        """Should find law by abbreviation."""
        result = search_laws("OR")
        assert result.total_results >= 1
        assert any(law.sr_number == "220" for law in result.results)

    def test_search_by_abbreviation_case_insensitive(self) -> None:
        """Should handle case-insensitive abbreviation search."""
        result = search_laws("or")
        assert result.total_results >= 1
        assert any(law.abbreviation == "OR" for law in result.results)

    def test_search_by_keyword(self) -> None:
        """Should find laws by keyword."""
        result = search_laws("Vertrag")
        assert result.total_results >= 1
        # Should find OR (Code of Obligations)
        assert any("220" in law.sr_number for law in result.results)

    def test_search_criminal_domain(self) -> None:
        """Should filter by legal domain."""
        result = search_laws("Straf", domain=LegalDomain.CRIMINAL_LAW)
        # All results should be in criminal law domain (SR 3xx)
        for law in result.results:
            assert law.sr_number.startswith("3")

    def test_search_returns_fedlex_url(self) -> None:
        """Results should include Fedlex URLs."""
        result = search_laws("ZGB")
        assert result.total_results >= 1
        for law in result.results:
            assert law.fedlex_url.startswith("https://www.fedlex.admin.ch")

    def test_search_with_language(self) -> None:
        """Should return results in specified language."""
        result = search_laws("OR", language=Language.FRENCH)
        assert result.language == Language.FRENCH

    def test_search_with_limit(self) -> None:
        """Should respect limit parameter."""
        result = search_laws("law", limit=3)
        assert len(result.results) <= 3

    def test_search_empty_query_raises(self) -> None:
        """Should raise ValueError for empty query."""
        with pytest.raises(ValueError, match="empty"):
            search_laws("")

    def test_search_whitespace_query_raises(self) -> None:
        """Should raise ValueError for whitespace-only query."""
        with pytest.raises(ValueError, match="empty"):
            search_laws("   ")

    def test_search_includes_timestamp(self) -> None:
        """Results should include search timestamp."""
        result = search_laws("OR")
        assert result.search_timestamp is not None
        assert "T" in result.search_timestamp  # ISO format

    def test_search_includes_notes(self) -> None:
        """Results should include informational notes."""
        result = search_laws("OR")
        assert len(result.notes) >= 1
        assert any("fedlex" in note.lower() for note in result.notes)


class TestGetLawBySrNumber:
    """Tests for get_law_by_sr_number function."""

    def test_lookup_known_law(self) -> None:
        """Should find law by SR number."""
        law = get_law_by_sr_number("220")
        assert law is not None
        assert law.sr_number == "220"
        assert law.abbreviation == "OR"

    def test_lookup_unknown_sr(self) -> None:
        """Should return basic entry for unknown SR number."""
        law = get_law_by_sr_number("999.999")
        assert law is not None
        assert law.sr_number == "999.999"
        assert law.abbreviation is None

    def test_lookup_with_language(self) -> None:
        """Should return entry in specified language."""
        law = get_law_by_sr_number("220", language=Language.FRENCH)
        assert law is not None
        assert law.language == Language.FRENCH
        assert "/fr" in law.fedlex_url


class TestGetCommonLawAbbreviations:
    """Tests for get_common_law_abbreviations function."""

    def test_returns_dict(self) -> None:
        """Should return a dictionary."""
        abbrs = get_common_law_abbreviations()
        assert isinstance(abbrs, dict)

    def test_contains_common_laws(self) -> None:
        """Should contain well-known Swiss laws."""
        abbrs = get_common_law_abbreviations()
        assert "OR" in abbrs
        assert "ZGB" in abbrs
        assert "StGB" in abbrs
        assert "ZPO" in abbrs
        assert "BV" in abbrs

    def test_sr_numbers_are_correct(self) -> None:
        """SR numbers should match known values."""
        abbrs = get_common_law_abbreviations()
        assert abbrs["OR"] == "220"
        assert abbrs["ZGB"] == "210"
        assert abbrs["StGB"] == "311.0"
        assert abbrs["BV"] == "101"

    def test_returns_copy(self) -> None:
        """Should return a copy, not the original dict."""
        abbrs1 = get_common_law_abbreviations()
        abbrs2 = get_common_law_abbreviations()
        abbrs1["TEST"] = "999"
        assert "TEST" not in abbrs2


class TestFedlexAPIError:
    """Tests for FedlexAPIError exception."""

    def test_error_with_message(self) -> None:
        """Should create error with message."""
        error = FedlexAPIError("Test error")
        assert error.message == "Test error"
        assert error.status_code is None

    def test_error_with_status_code(self) -> None:
        """Should create error with status code."""
        error = FedlexAPIError("API failed", status_code=500)
        assert error.message == "API failed"
        assert error.status_code == 500

    def test_error_string_representation(self) -> None:
        """Should have correct string representation."""
        error = FedlexAPIError("Test error")
        assert str(error) == "Test error"


class TestSearchLawsIntegration:
    """Integration tests for search_laws."""

    def test_search_labor_law(self) -> None:
        """Should find labor law related entries."""
        result = search_laws("Arbeit", domain=LegalDomain.HEALTH)
        # ArG is in SR 8 (Health domain includes employment)
        assert result.total_results >= 1

    def test_search_data_protection(self) -> None:
        """Should find data protection law."""
        result = search_laws("Datenschutz")
        assert result.total_results >= 1
        assert any(law.abbreviation == "DSG" for law in result.results)

    def test_search_civil_code(self) -> None:
        """Should find civil code."""
        result = search_laws("ZGB")
        assert result.total_results >= 1
        law = result.results[0]
        assert law.sr_number == "210"
        assert "Zivilgesetzbuch" in law.title

    def test_search_federal_constitution(self) -> None:
        """Should find Federal Constitution."""
        result = search_laws("BV")
        assert result.total_results >= 1
        law = result.results[0]
        assert law.sr_number == "101"
        assert law.law_type == "Federal Constitution"
