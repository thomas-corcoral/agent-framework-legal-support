"""Swiss Legal Support Tools.

This module provides utility tools for the Swiss Legal Support agentic workflow.
"""

from legal_support.tools.detect_language import (
    LanguageDetectionResult,
    SupportedLanguage,
    detect_language,
    get_preferred_swiss_language,
)
from legal_support.tools.estimate_costs import (
    Canton,
    CostBreakdown,
    CostEstimationResult,
    CourtLevel,
    ProceedingType,
    estimate_costs,
    get_free_proceedings,
)
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
    search_laws_async,
)

__all__ = [
    # Language detection
    "LanguageDetectionResult",
    "SupportedLanguage",
    "detect_language",
    "get_preferred_swiss_language",
    # Cost estimation
    "Canton",
    "CostBreakdown",
    "CostEstimationResult",
    "CourtLevel",
    "ProceedingType",
    "estimate_costs",
    "get_free_proceedings",
    # Law search
    "FedlexAPIError",
    "Language",
    "LawArticle",
    "LawEntry",
    "LawSearchResult",
    "LawType",
    "LegalDomain",
    "get_common_law_abbreviations",
    "get_law_by_sr_number",
    "search_laws",
    "search_laws_async",
]
