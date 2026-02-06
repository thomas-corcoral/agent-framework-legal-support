"""Law search tool for Swiss Legal Support.

This module provides functionality to search Swiss federal and cantonal laws
through the Fedlex API (Federal Chancellery's legal information platform).

Fedlex (fedlex.admin.ch) is the official publication platform for Swiss federal law,
including the Federal Constitution, federal acts, ordinances, and international treaties.
"""

from __future__ import annotations

import logging
from datetime import date
from enum import Enum
from typing import Annotated

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class LegalDomain(str, Enum):
    """Legal domains in Swiss law (based on SR classification).

    The Systematic Compilation (SR - Systematische Rechtssammlung) organizes
    Swiss federal law into numbered domains.
    """

    CONSTITUTION = "1"  # State - People - Authorities (SR 1)
    PRIVATE_LAW = "2"  # Private Law - Civil Procedure - Enforcement (SR 2)
    CRIMINAL_LAW = "3"  # Criminal Law - Criminal Procedure - Execution (SR 3)
    EDUCATION = "4"  # Education - Science - Culture (SR 4)
    DEFENSE = "5"  # National Defense (SR 5)
    FINANCE = "6"  # Finance (SR 6)
    PUBLIC_WORKS = "7"  # Public Works - Energy - Transport (SR 7)
    HEALTH = "8"  # Health - Employment - Social Security (SR 8)
    ECONOMY = "9"  # Economy - Technical Cooperation (SR 9)
    INTERNATIONAL = "0"  # International Treaties (SR 0)
    ALL = "all"  # Search across all domains


class LawType(str, Enum):
    """Types of Swiss legal documents."""

    FEDERAL_ACT = "federal_act"  # Bundesgesetz (BG)
    ORDINANCE = "ordinance"  # Verordnung (V)
    FEDERAL_DECREE = "federal_decree"  # Bundesbeschluss (BB)
    CONSTITUTION = "constitution"  # Verfassung (BV)
    INTERNATIONAL_TREATY = "international_treaty"  # Internationaler Vertrag
    ALL = "all"  # All types


class Language(str, Enum):
    """Languages for law search results."""

    GERMAN = "de"
    FRENCH = "fr"
    ITALIAN = "it"
    ROMANSH = "rm"
    ENGLISH = "en"


class LawArticle(BaseModel):
    """A specific article within a law."""

    article_number: str = Field(description="Article number (e.g., 'Art. 8', 'Art. 261bis')")
    title: str | None = Field(default=None, description="Article title if available")
    content: str = Field(description="Full text content of the article")
    paragraph: str | None = Field(default=None, description="Specific paragraph if applicable")


class LawEntry(BaseModel):
    """A law entry from the search results."""

    sr_number: str = Field(description="Systematic compilation number (e.g., '220' for OR)")
    title: str = Field(description="Official title of the law")
    abbreviation: str | None = Field(
        default=None, description="Common abbreviation (e.g., 'OR', 'ZGB', 'StGB')"
    )
    law_type: str = Field(description="Type of legal document")
    enactment_date: date | None = Field(default=None, description="Date of enactment")
    entry_into_force: date | None = Field(
        default=None, description="Date when law entered into force"
    )
    language: Language = Field(description="Language of this entry")
    fedlex_url: str = Field(description="URL to the full law on Fedlex")
    relevant_articles: list[LawArticle] = Field(
        default_factory=list, description="Relevant articles matching the search query"
    )
    summary: str | None = Field(default=None, description="Brief summary of the law's purpose")

    @property
    def full_citation(self) -> str:
        """Generate a proper legal citation."""
        if self.abbreviation:
            return f"{self.abbreviation} (SR {self.sr_number})"
        return f"SR {self.sr_number}"


class LawSearchResult(BaseModel):
    """Result of a law search query."""

    query: str = Field(description="Original search query")
    domain: LegalDomain = Field(description="Legal domain searched")
    language: Language = Field(description="Language of results")
    total_results: int = Field(ge=0, description="Total number of results found")
    results: list[LawEntry] = Field(default_factory=list, description="List of matching laws")
    search_timestamp: str = Field(description="ISO timestamp of the search")
    suggestions: list[str] = Field(default_factory=list, description="Related search suggestions")
    notes: list[str] = Field(default_factory=list, description="Additional notes about the search")


# Mapping of common Swiss law abbreviations to SR numbers
COMMON_LAWS = {
    # Private Law (SR 2)
    "ZGB": "210",  # Zivilgesetzbuch - Civil Code
    "OR": "220",  # Obligationenrecht - Code of Obligations
    "SchKG": "281.1",  # Schuldbetreibungs- und Konkursgesetz - Debt Collection
    "IPRG": "291",  # Internationales Privatrecht - Private International Law
    "ZPO": "272",  # Zivilprozessordnung - Civil Procedure Code
    # Criminal Law (SR 3)
    "StGB": "311.0",  # Strafgesetzbuch - Criminal Code
    "StPO": "312.0",  # Strafprozessordnung - Criminal Procedure Code
    "JStG": "311.1",  # Jugendstrafgesetz - Juvenile Criminal Law
    # Constitutional Law (SR 1)
    "BV": "101",  # Bundesverfassung - Federal Constitution
    "ParlG": "171.10",  # Parlamentsgesetz - Parliament Act
    "BGG": "173.110",  # Bundesgerichtsgesetz - Federal Court Act
    "VwVG": "172.021",  # Verwaltungsverfahrensgesetz - Administrative Procedure Act
    # Labor Law (SR 8)
    "ArG": "822.11",  # Arbeitsgesetz - Labor Act
    "AVG": "823.11",  # Arbeitsvermittlungsgesetz - Employment Services Act
    "AVIG": "837.0",  # Arbeitslosenversicherungsgesetz - Unemployment Insurance
    "UVG": "832.20",  # Unfallversicherungsgesetz - Accident Insurance
    # Social Security (SR 8)
    "AHVG": "831.10",  # AHV-Gesetz - Old-Age Insurance
    "IVG": "831.20",  # Invalidenversicherungsgesetz - Disability Insurance
    "KVG": "832.10",  # Krankenversicherungsgesetz - Health Insurance
    "BVG": "831.40",  # Berufliche Vorsorge - Occupational Pensions
    # Other important laws
    "DSG": "235.1",  # Datenschutzgesetz - Data Protection Act
    "MiG": "221.213.11",  # Mietrecht - Tenancy Law (part of OR)
    "ATSG": "830.1",  # Allgemeines Sozialversicherungsgesetz
}

# Fedlex API configuration
FEDLEX_API_BASE = "https://fedlex.data.admin.ch/sparql"
FEDLEX_WEB_BASE = "https://www.fedlex.admin.ch/eli/cc"

# Proxy configuration for HTTP requests
HTTP_PROXY = "http://127.0.0.1:8887"


class FedlexAPIError(Exception):
    """Exception raised when Fedlex API calls fail."""

    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


def _build_sparql_query(
    search_term: str,
    domain: LegalDomain,
    law_type: LawType,
    language: Language,
    limit: int,
) -> str:
    """Build a SPARQL query for Fedlex.

    Fedlex provides a SPARQL endpoint for querying Swiss federal legislation.
    """
    # Language code mapping for Fedlex
    lang_code = language.value

    # Domain filter
    domain_filter = ""
    if domain != LegalDomain.ALL:
        domain_filter = f'FILTER(STRSTARTS(?srNumber, "{domain.value}"))'

    # Build the SPARQL query
    query = f"""
    PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX eli: <http://data.europa.eu/eli/ontology#>

    SELECT DISTINCT ?law ?srNumber ?title ?abbreviation ?dateDocument ?dateEntryInForce
    WHERE {{
        ?law a eli:LegalResource ;
             eli:is_realized_by ?expression .
        ?expression eli:language <http://publications.europa.eu/resource/authority/language/{lang_code.upper()}> ;
                    eli:title ?title .
        ?law jolux:classifiedByTaxonomyEntry ?taxonomyEntry .
        ?taxonomyEntry skos:notation ?srNumber .

        OPTIONAL {{ ?law eli:date_document ?dateDocument }}
        OPTIONAL {{ ?law eli:date_entry_in_force ?dateEntryInForce }}
        OPTIONAL {{ ?expression eli:title_short ?abbreviation }}

        FILTER(CONTAINS(LCASE(?title), LCASE("{search_term}")))
        {domain_filter}
    }}
    ORDER BY ?srNumber
    LIMIT {limit}
    """
    return query


def _parse_fedlex_response(
    response_data: dict,
    search_term: str,
    language: Language,
) -> list[LawEntry]:
    """Parse the Fedlex SPARQL response into LawEntry objects."""
    results = []

    bindings = response_data.get("results", {}).get("bindings", [])

    for binding in bindings:
        sr_number = binding.get("srNumber", {}).get("value", "")
        title = binding.get("title", {}).get("value", "")
        abbreviation = binding.get("abbreviation", {}).get("value")

        # Parse dates if available
        enactment_date = None
        entry_into_force = None

        if "dateDocument" in binding:
            try:
                enactment_date = date.fromisoformat(binding["dateDocument"]["value"][:10])
            except (ValueError, KeyError):
                pass

        if "dateEntryInForce" in binding:
            try:
                entry_into_force = date.fromisoformat(binding["dateEntryInForce"]["value"][:10])
            except (ValueError, KeyError):
                pass

        # Build Fedlex URL
        fedlex_url = f"{FEDLEX_WEB_BASE}/{sr_number}/{language.value}"

        # Determine law type from SR number
        law_type = _determine_law_type(sr_number)

        entry = LawEntry(
            sr_number=sr_number,
            title=title,
            abbreviation=abbreviation,
            law_type=law_type,
            enactment_date=enactment_date,
            entry_into_force=entry_into_force,
            language=language,
            fedlex_url=fedlex_url,
            relevant_articles=[],
            summary=None,
        )
        results.append(entry)

    return results


def _determine_law_type(sr_number: str) -> str:
    """Determine the type of law based on SR number patterns."""
    if sr_number.startswith("0"):
        return "International Treaty"
    elif sr_number == "101":
        return "Federal Constitution"
    elif "." not in sr_number:
        return "Federal Act"
    else:
        # Check common patterns
        parts = sr_number.split(".")
        if len(parts) >= 2 and int(parts[-1]) > 100:
            return "Ordinance"
        return "Federal Act"


def _get_law_by_abbreviation(
    abbreviation: str,
    language: Language,
) -> LawEntry | None:
    """Look up a law by its common abbreviation."""
    abbr_upper = abbreviation.upper()
    if abbr_upper not in COMMON_LAWS:
        return None

    sr_number = COMMON_LAWS[abbr_upper]
    fedlex_url = f"{FEDLEX_WEB_BASE}/{sr_number}/{language.value}"

    # Common law titles (German)
    titles = {
        "ZGB": "Schweizerisches Zivilgesetzbuch",
        "OR": "Bundesgesetz betreffend die Ergänzung des Schweizerischen Zivilgesetzbuches (Obligationenrecht)",
        "StGB": "Schweizerisches Strafgesetzbuch",
        "StPO": "Schweizerische Strafprozessordnung",
        "ZPO": "Schweizerische Zivilprozessordnung",
        "BV": "Bundesverfassung der Schweizerischen Eidgenossenschaft",
        "BGG": "Bundesgesetz über das Bundesgericht",
        "SchKG": "Bundesgesetz über Schuldbetreibung und Konkurs",
        "ArG": "Bundesgesetz über die Arbeit in Industrie, Gewerbe und Handel",
        "KVG": "Bundesgesetz über die Krankenversicherung",
        "DSG": "Bundesgesetz über den Datenschutz",
    }

    return LawEntry(
        sr_number=sr_number,
        title=titles.get(abbr_upper, f"Swiss Law {abbr_upper}"),
        abbreviation=abbr_upper,
        law_type="Federal Act" if abbr_upper != "BV" else "Federal Constitution",
        enactment_date=None,
        entry_into_force=None,
        language=language,
        fedlex_url=fedlex_url,
        relevant_articles=[],
        summary=None,
    )


def _search_mock_data(
    query: str,
    domain: LegalDomain,
    language: Language,
    limit: int,
) -> list[LawEntry]:
    """Provide mock search results for demonstration and offline testing.

    This function returns relevant Swiss laws based on common legal queries.
    In production, this would be replaced by actual Fedlex API calls.
    """
    query_lower = query.lower()
    results = []

    # Mock database of common Swiss laws with German titles
    mock_laws = [
        {
            "sr_number": "220",
            "title": "Bundesgesetz betreffend die Ergänzung des Schweizerischen Zivilgesetzbuches (Fünfter Teil: Obligationenrecht)",
            "abbreviation": "OR",
            "law_type": "Federal Act",
            "keywords": [
                "contract",
                "vertrag",
                "obligation",
                "haftung",
                "liability",
                "kauf",
                "sale",
                "miete",
                "rent",
                "arbeit",
                "work",
                "employment",
            ],
            "summary": "Swiss Code of Obligations governing contracts, torts, and commercial law.",
        },
        {
            "sr_number": "210",
            "title": "Schweizerisches Zivilgesetzbuch",
            "abbreviation": "ZGB",
            "law_type": "Federal Act",
            "keywords": [
                "civil",
                "person",
                "family",
                "ehe",
                "marriage",
                "divorce",
                "scheidung",
                "inheritance",
                "erbschaft",
                "property",
                "eigentum",
            ],
            "summary": "Swiss Civil Code governing personal status, family law, inheritance, and property.",
        },
        {
            "sr_number": "311.0",
            "title": "Schweizerisches Strafgesetzbuch",
            "abbreviation": "StGB",
            "law_type": "Federal Act",
            "keywords": [
                "criminal",
                "straf",
                "crime",
                "theft",
                "diebstahl",
                "fraud",
                "betrug",
                "assault",
                "körperverletzung",
            ],
            "summary": "Swiss Criminal Code defining crimes and penalties.",
        },
        {
            "sr_number": "272",
            "title": "Schweizerische Zivilprozessordnung",
            "abbreviation": "ZPO",
            "law_type": "Federal Act",
            "keywords": [
                "civil procedure",
                "prozess",
                "court",
                "gericht",
                "klage",
                "lawsuit",
                "appeal",
                "berufung",
            ],
            "summary": "Swiss Civil Procedure Code governing civil litigation.",
        },
        {
            "sr_number": "312.0",
            "title": "Schweizerische Strafprozessordnung",
            "abbreviation": "StPO",
            "law_type": "Federal Act",
            "keywords": [
                "criminal procedure",
                "strafverfahren",
                "prosecution",
                "investigation",
                "ermittlung",
            ],
            "summary": "Swiss Criminal Procedure Code governing criminal proceedings.",
        },
        {
            "sr_number": "101",
            "title": "Bundesverfassung der Schweizerischen Eidgenossenschaft",
            "abbreviation": "BV",
            "law_type": "Federal Constitution",
            "keywords": [
                "constitution",
                "verfassung",
                "grundrecht",
                "fundamental",
                "rights",
                "freedom",
                "freiheit",
                "equality",
                "gleichheit",
            ],
            "summary": "Swiss Federal Constitution establishing fundamental rights and state structure.",
        },
        {
            "sr_number": "822.11",
            "title": "Bundesgesetz über die Arbeit in Industrie, Gewerbe und Handel",
            "abbreviation": "ArG",
            "law_type": "Federal Act",
            "keywords": [
                "labor",
                "arbeit",
                "employment",
                "working hours",
                "arbeitszeit",
                "protection",
                "schutz",
            ],
            "summary": "Swiss Labor Act regulating working conditions and employee protection.",
        },
        {
            "sr_number": "281.1",
            "title": "Bundesgesetz über Schuldbetreibung und Konkurs",
            "abbreviation": "SchKG",
            "law_type": "Federal Act",
            "keywords": [
                "debt",
                "schuld",
                "betreibung",
                "collection",
                "bankruptcy",
                "konkurs",
                "insolvency",
            ],
            "summary": "Swiss Debt Collection and Bankruptcy Act.",
        },
        {
            "sr_number": "173.110",
            "title": "Bundesgesetz über das Bundesgericht",
            "abbreviation": "BGG",
            "law_type": "Federal Act",
            "keywords": ["federal court", "bundesgericht", "appeal", "beschwerde", "supreme court"],
            "summary": "Federal Court Act governing Switzerland's highest court.",
        },
        {
            "sr_number": "832.10",
            "title": "Bundesgesetz über die Krankenversicherung",
            "abbreviation": "KVG",
            "law_type": "Federal Act",
            "keywords": ["health", "insurance", "kranken", "versicherung", "medical", "healthcare"],
            "summary": "Swiss Health Insurance Act establishing mandatory health insurance.",
        },
        {
            "sr_number": "235.1",
            "title": "Bundesgesetz über den Datenschutz",
            "abbreviation": "DSG",
            "law_type": "Federal Act",
            "keywords": [
                "data",
                "daten",
                "privacy",
                "protection",
                "schutz",
                "personal",
                "persönlich",
            ],
            "summary": "Swiss Data Protection Act governing personal data processing.",
        },
        {
            "sr_number": "831.10",
            "title": "Bundesgesetz über die Alters- und Hinterlassenenversicherung",
            "abbreviation": "AHVG",
            "law_type": "Federal Act",
            "keywords": [
                "pension",
                "retirement",
                "ahv",
                "old age",
                "alter",
                "social security",
                "sozialversicherung",
            ],
            "summary": "Swiss Old-Age and Survivors' Insurance Act (first pillar pension).",
        },
        {
            "sr_number": "831.40",
            "title": "Bundesgesetz über die berufliche Alters-, Hinterlassenen- und Invalidenvorsorge",
            "abbreviation": "BVG",
            "law_type": "Federal Act",
            "keywords": ["pension", "occupational", "beruflich", "vorsorge", "retirement", "bvg"],
            "summary": "Swiss Occupational Pensions Act (second pillar pension).",
        },
        {
            "sr_number": "221.213.11",
            "title": "Mietrecht (Art. 253-274g OR)",
            "abbreviation": "Mietrecht",
            "law_type": "Federal Act",
            "keywords": [
                "rent",
                "miete",
                "tenancy",
                "tenant",
                "mieter",
                "landlord",
                "vermieter",
                "lease",
            ],
            "summary": "Swiss Tenancy Law provisions within the Code of Obligations.",
        },
        {
            "sr_number": "830.1",
            "title": "Bundesgesetz über den Allgemeinen Teil des Sozialversicherungsrechts",
            "abbreviation": "ATSG",
            "law_type": "Federal Act",
            "keywords": ["social", "sozial", "insurance", "versicherung", "general", "allgemein"],
            "summary": "General Social Insurance Act providing common rules for social security.",
        },
    ]

    # Check for abbreviation matches first
    abbr_match = _get_law_by_abbreviation(query, language)
    if abbr_match:
        results.append(abbr_match)
        return results[:limit]

    # Search by keywords
    for law in mock_laws:
        # Check if query matches any keywords
        if any(kw in query_lower for kw in law["keywords"]) or query_lower in law["title"].lower():
            # Apply domain filter
            if domain != LegalDomain.ALL:
                if not law["sr_number"].startswith(domain.value):
                    continue

            entry = LawEntry(
                sr_number=law["sr_number"],
                title=law["title"],
                abbreviation=law["abbreviation"],
                law_type=law["law_type"],
                enactment_date=None,
                entry_into_force=None,
                language=language,
                fedlex_url=f"{FEDLEX_WEB_BASE}/{law['sr_number']}/{language.value}",
                relevant_articles=[],
                summary=law["summary"],
            )
            results.append(entry)

            if len(results) >= limit:
                break

    return results


async def search_laws_async(
    query: Annotated[str, Field(description="Search query (keywords, law name, or abbreviation)")],
    domain: Annotated[
        LegalDomain, Field(description="Legal domain to search within")
    ] = LegalDomain.ALL,
    law_type: Annotated[
        LawType, Field(description="Type of legal document to search for")
    ] = LawType.ALL,
    language: Annotated[
        Language, Field(description="Language for search results")
    ] = Language.GERMAN,
    limit: Annotated[
        int, Field(ge=1, le=50, description="Maximum number of results to return")
    ] = 10,
    include_articles: Annotated[
        bool, Field(description="Whether to include relevant article excerpts")
    ] = False,
    use_mock: Annotated[
        bool, Field(description="Use mock data instead of live API (for testing)")
    ] = True,
) -> LawSearchResult:
    """Search Swiss federal laws through the Fedlex API (async version).

    This function queries the Fedlex database to find relevant Swiss laws
    based on keywords, legal domain, or specific law references.

    Args:
        query: Search query - can be keywords, law title, or abbreviation (e.g., "OR", "ZGB")
        domain: Legal domain to restrict search (based on SR classification)
        law_type: Type of legal document to search for
        language: Language for search results (de, fr, it, rm, en)
        limit: Maximum number of results to return (1-50)
        include_articles: Whether to fetch and include relevant article excerpts
        use_mock: Use mock data for testing (default True for reliability)

    Returns:
        LawSearchResult containing matching laws, metadata, and suggestions.

    Examples:
        >>> result = await search_laws_async("Arbeitsvertrag")
        >>> for law in result.results:
        ...     print(f"{law.abbreviation}: {law.title}")
        OR: Bundesgesetz betreffend die Ergänzung des Schweizerischen Zivilgesetzbuches

        >>> result = await search_laws_async("OR")  # Search by abbreviation
        >>> result.results[0].sr_number
        '220'

        >>> result = await search_laws_async(
        ...     "Strafrecht",
        ...     domain=LegalDomain.CRIMINAL_LAW,
        ...     language=Language.GERMAN,
        ... )
    """
    from datetime import datetime

    if not query or not query.strip():
        raise ValueError("Search query cannot be empty")

    query = query.strip()
    notes: list[str] = []
    suggestions: list[str] = []

    # Search for laws
    if use_mock:
        results = _search_mock_data(query, domain, language, limit)
        notes.append("Results from local database. For latest information, consult fedlex.admin.ch")
    else:
        # Build and execute SPARQL query against Fedlex
        sparql_query = _build_sparql_query(query, domain, law_type, language, limit)

        try:
            async with httpx.AsyncClient(
                timeout=30.0,
                proxy=HTTP_PROXY,
            ) as client:
                response = await client.get(
                    FEDLEX_API_BASE,
                    params={
                        "query": sparql_query,
                        "format": "json",
                    },
                    headers={
                        "Accept": "application/sparql-results+json",
                        "User-Agent": "SwissLegalSupport/1.0",
                    },
                )
                response.raise_for_status()
                data = response.json()
                results = _parse_fedlex_response(data, query, language)

        except httpx.HTTPStatusError as e:
            logger.error(f"Fedlex API error: {e.response.status_code}")
            raise FedlexAPIError(
                f"Fedlex API returned error: {e.response.status_code}",
                status_code=e.response.status_code,
            ) from e
        except httpx.RequestError as e:
            logger.error(f"Fedlex API request failed: {e}")
            # Fall back to mock data
            results = _search_mock_data(query, domain, language, limit)
            notes.append("Live API unavailable. Results from local database.")

    # Generate suggestions for related searches
    if not results:
        suggestions = _generate_suggestions(query, domain)
        notes.append(
            f"No results found for '{query}'. Try the suggested searches or broaden your query."
        )
    elif len(results) == 1:
        # Suggest related laws
        related = _get_related_laws(results[0].sr_number)
        suggestions.extend(related)

    # Add standard notes
    notes.append("For authoritative text, always consult the official version at fedlex.admin.ch")

    return LawSearchResult(
        query=query,
        domain=domain,
        language=language,
        total_results=len(results),
        results=results,
        search_timestamp=datetime.utcnow().isoformat() + "Z",
        suggestions=suggestions,
        notes=notes,
    )


def search_laws(
    query: Annotated[str, Field(description="Search query (keywords, law name, or abbreviation)")],
    domain: Annotated[
        LegalDomain, Field(description="Legal domain to search within")
    ] = LegalDomain.ALL,
    law_type: Annotated[
        LawType, Field(description="Type of legal document to search for")
    ] = LawType.ALL,
    language: Annotated[
        Language, Field(description="Language for search results")
    ] = Language.GERMAN,
    limit: Annotated[
        int, Field(ge=1, le=50, description="Maximum number of results to return")
    ] = 10,
    include_articles: Annotated[
        bool, Field(description="Whether to include relevant article excerpts")
    ] = False,
) -> LawSearchResult:
    """Search Swiss federal laws through the Fedlex API (synchronous version).

    This function queries the Fedlex database to find relevant Swiss laws
    based on keywords, legal domain, or specific law references.

    Args:
        query: Search query - can be keywords, law title, or abbreviation (e.g., "OR", "ZGB")
        domain: Legal domain to restrict search (based on SR classification)
        law_type: Type of legal document to search for
        language: Language for search results (de, fr, it, rm, en)
        limit: Maximum number of results to return (1-50)
        include_articles: Whether to fetch and include relevant article excerpts

    Returns:
        LawSearchResult containing matching laws, metadata, and suggestions.

    Examples:
        >>> result = search_laws("Arbeitsvertrag")
        >>> for law in result.results:
        ...     print(f"{law.abbreviation}: {law.title}")
        OR: Bundesgesetz betreffend die Ergänzung des Schweizerischen Zivilgesetzbuches

        >>> result = search_laws("OR")  # Search by abbreviation
        >>> result.results[0].sr_number
        '220'

        >>> result = search_laws(
        ...     "Miete",
        ...     domain=LegalDomain.PRIVATE_LAW,
        ...     language=Language.GERMAN,
        ... )
    """
    import asyncio

    # Run the async version synchronously using asyncio.run()
    # This is the recommended approach for Python 3.7+
    return asyncio.run(
        search_laws_async(
            query=query,
            domain=domain,
            law_type=law_type,
            language=language,
            limit=limit,
            include_articles=include_articles,
            use_mock=True,  # Default to mock for sync version
        )
    )


def _generate_suggestions(query: str, domain: LegalDomain) -> list[str]:
    """Generate search suggestions when no results are found."""
    suggestions = []

    # Suggest common abbreviations
    common = ["OR", "ZGB", "StGB", "ZPO", "ArG", "KVG", "DSG"]
    suggestions.append(f"Try searching for a common law abbreviation: {', '.join(common)}")

    # Domain-specific suggestions
    domain_suggestions = {
        LegalDomain.PRIVATE_LAW: ["Vertrag", "Haftung", "Eigentum", "Erbschaft"],
        LegalDomain.CRIMINAL_LAW: ["Straftat", "Betrug", "Diebstahl", "Körperverletzung"],
        LegalDomain.CONSTITUTION: ["Grundrechte", "Verfassung", "Freiheit", "Gleichheit"],
        LegalDomain.HEALTH: ["Versicherung", "Kranken", "Unfall", "Invalidität"],
    }

    if domain in domain_suggestions:
        terms = domain_suggestions[domain]
        suggestions.append(f"Try domain-specific terms: {', '.join(terms)}")

    return suggestions


def _get_related_laws(sr_number: str) -> list[str]:
    """Get suggestions for related laws based on SR number."""
    related = {
        "220": ["ZGB (SR 210) - Civil Code", "SchKG (SR 281.1) - Debt Collection"],
        "210": ["OR (SR 220) - Code of Obligations", "ZPO (SR 272) - Civil Procedure"],
        "311.0": [
            "StPO (SR 312.0) - Criminal Procedure",
            "JStG (SR 311.1) - Juvenile Criminal Law",
        ],
        "272": ["OR (SR 220) - Code of Obligations", "BGG (SR 173.110) - Federal Court Act"],
    }
    return related.get(sr_number, [])


def get_law_by_sr_number(
    sr_number: Annotated[str, Field(description="Systematic compilation number (e.g., '220')")],
    language: Annotated[Language, Field(description="Language for the result")] = Language.GERMAN,
) -> LawEntry | None:
    """Look up a specific law by its SR (Systematic Compilation) number.

    Args:
        sr_number: The SR number of the law (e.g., "220" for OR, "311.0" for StGB)
        language: Language for the result

    Returns:
        LawEntry if found, None otherwise.

    Examples:
        >>> law = get_law_by_sr_number("220")
        >>> law.abbreviation
        'OR'
        >>> law.title
        'Bundesgesetz betreffend die Ergänzung des Schweizerischen Zivilgesetzbuches...'
    """
    # Reverse lookup from SR number to abbreviation
    sr_to_abbr = {v: k for k, v in COMMON_LAWS.items()}

    abbreviation = sr_to_abbr.get(sr_number)
    if abbreviation:
        return _get_law_by_abbreviation(abbreviation, language)

    # If not in common laws, construct a basic entry
    fedlex_url = f"{FEDLEX_WEB_BASE}/{sr_number}/{language.value}"

    return LawEntry(
        sr_number=sr_number,
        title=f"Swiss Federal Law SR {sr_number}",
        abbreviation=None,
        law_type=_determine_law_type(sr_number),
        enactment_date=None,
        entry_into_force=None,
        language=language,
        fedlex_url=fedlex_url,
        relevant_articles=[],
        summary=None,
    )


def get_common_law_abbreviations() -> dict[str, str]:
    """Get a dictionary of common Swiss law abbreviations and their SR numbers.

    Returns:
        Dictionary mapping abbreviations (e.g., "OR") to SR numbers (e.g., "220").

    Examples:
        >>> abbrs = get_common_law_abbreviations()
        >>> abbrs["OR"]
        '220'
        >>> abbrs["StGB"]
        '311.0'
    """
    return COMMON_LAWS.copy()
