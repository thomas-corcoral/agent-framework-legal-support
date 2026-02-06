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
from legal_support.tools.semantic_case_search import (
    CaseDecision,
    CaseSearchResult,
    CourtChamber,
    LegalArea,
    VectorIndex,
    get_index,
    semantic_case_search,
    semantic_case_search_async,
)

__all__ = [
    "Canton",
    "CaseDecision",
    "CaseSearchResult",
    "CostBreakdown",
    "CostEstimationResult",
    "CourtChamber",
    "CourtLevel",
    "FedlexAPIError",
    "Language",
    "LanguageDetectionResult",
    "LawArticle",
    "LawEntry",
    "LawSearchResult",
    "LawType",
    "LegalArea",
    "LegalDomain",
    "ProceedingType",
    "SupportedLanguage",
    "VectorIndex",
    "detect_language",
    "estimate_costs",
    "get_common_law_abbreviations",
    "get_free_proceedings",
    "get_index",
    "get_law_by_sr_number",
    "get_preferred_swiss_language",
    "search_laws",
    "search_laws_async",
    "semantic_case_search",
    "semantic_case_search_async",
]
