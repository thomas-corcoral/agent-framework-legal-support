# Swiss Legal Support - Agents and Tools Summary

## Agents Overview (9 total)

| # | Agent | Primary Responsibility | Key Output |
|---|-------|----------------------|------------|
| 1 | **Orchestrator Agent** | Coordinate workflow, manage state | Final response delivery |
| 2 | **Intake Agent** | Clarify and structure user question | Structured question object |
| 3 | **Classifier Agent** | Identify legal domain and jurisdiction | Classification tags |
| 4 | **Law Article Agent** | Search and retrieve relevant laws | List of applicable laws |
| 5 | **Case Law Agent** | Find similar historical cases | List of precedents |
| 6 | **Outcome Prediction Agent** | Analyze likely outcomes | Outcome assessment |
| 7 | **Next Steps Agent** | Determine actionable guidance | Action items and resources |
| 8 | **Response Synthesis Agent** | Compile final response | Complete user response |
| 9 | **Quality Assurance Agent** | Validate completeness and accuracy | Approval/Revision decision |

---

## Tools Overview (6 total)

### Data Retrieval Tools (2)

| Tool | Description | Used By | Data Source |
|------|-------------|---------|-------------|
| [`search_laws`](#search_laws-tool) | Search Swiss federal law databases | Law Article Agent | Fedlex API |
| `semantic_case_search` | Vector similarity search for cases | Case Law Agent | Vector DB |

### Analysis Tools (2)

| Tool | Description | Used By | Implementation |
|------|-------------|---------|----------------|
| `analyze_legal_strength` | Assess case strength | Outcome Prediction Agent | LLM-based |
| `compare_to_precedents` | Compare with similar cases | Outcome Prediction Agent | Semantic similarity |

### Utility Tools (2)

| Tool | Description | Used By | Implementation |
|------|-------------|---------|----------------|
| `detect_language` | Identify user language (DE/FR/IT/EN) | Intake Agent | langdetect |
| `estimate_costs` | Estimate procedural costs | Next Steps Agent | Fee schedules |

---

## Agent-Tool Matrix

| Agent | Tools |
|-------|-------|
| Orchestrator Agent | None (coordination only) |
| Intake Agent | `detect_language` |
| Classifier Agent | None |
| Law Article Agent | `search_laws` |
| Case Law Agent | `semantic_case_search` |
| Outcome Prediction Agent | `analyze_legal_strength`, `compare_to_precedents` |
| Next Steps Agent | `estimate_costs` |
| Response Synthesis Agent | None |
| Quality Assurance Agent | None |

---

## Data Flow Summary

```
User Question
    │
    ▼
┌─────────────────┐
│ Intake Agent    │──► Structured Question
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Classifier      │──► Domain + Jurisdiction
└─────────────────┘
    │
    ├────────────────────┬────────────────────┐
    ▼                    ▼                    ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│ Law Article │   │ Case Law    │   │ Outcome     │
│ Agent       │   │ Agent       │   │ Prediction  │
└─────────────┘   └─────────────┘   └─────────────┘
    │                    │                    │
    └────────────────────┼────────────────────┘
                         ▼
              ┌─────────────────┐
              │ Response        │
              │ Synthesis Agent │
              └─────────────────┘
                         │
                         ▼
              ┌─────────────────┐
              │ Next Steps      │
              │ Agent           │
              └─────────────────┘
                         │
                         ▼
              ┌─────────────────┐
              │ Quality         │
              │ Assurance Agent │
              └─────────────────┘
                        │
                        ▼
                 Final Response
```

---

## Tool Specifications

### `search_laws` Tool

**Module:** [`legal_support.tools.search_laws`](../../src/legal_support/tools/search_laws.py)

**Purpose:** Search Swiss federal and cantonal laws through the Fedlex API (Federal Chancellery's legal information platform).

#### Function Signatures

```python
def search_laws(
   query: str,                           # Search query (keywords, law name, or abbreviation)
   domain: LegalDomain = LegalDomain.ALL,  # Legal domain to search within
   law_type: LawType = LawType.ALL,        # Type of legal document
   language: Language = Language.GERMAN,   # Language for results (de/fr/it/rm/en)
   limit: int = 10,                        # Max results (1-50)
   include_articles: bool = False,         # Include relevant article excerpts
) -> LawSearchResult
```

```python
async def search_laws_async(
   query: str,
   domain: LegalDomain = LegalDomain.ALL,
   law_type: LawType = LawType.ALL,
   language: Language = Language.GERMAN,
   limit: int = 10,
   include_articles: bool = False,
   use_mock: bool = True,  # Use mock data for testing
) -> LawSearchResult
```

#### Enums

**`LegalDomain`** - Swiss law SR classification domains:
| Value | SR Number | Description |
|-------|-----------|-------------|
| `CONSTITUTION` | 1 | State - People - Authorities |
| `PRIVATE_LAW` | 2 | Private Law - Civil Procedure - Enforcement |
| `CRIMINAL_LAW` | 3 | Criminal Law - Criminal Procedure - Execution |
| `EDUCATION` | 4 | Education - Science - Culture |
| `DEFENSE` | 5 | National Defense |
| `FINANCE` | 6 | Finance |
| `PUBLIC_WORKS` | 7 | Public Works - Energy - Transport |
| `HEALTH` | 8 | Health - Employment - Social Security |
| `ECONOMY` | 9 | Economy - Technical Cooperation |
| `INTERNATIONAL` | 0 | International Treaties |
| `ALL` | all | Search across all domains |

**`LawType`** - Types of Swiss legal documents:
| Value | Description |
|-------|-------------|
| `FEDERAL_ACT` | Bundesgesetz (BG) |
| `ORDINANCE` | Verordnung (V) |
| `FEDERAL_DECREE` | Bundesbeschluss (BB) |
| `CONSTITUTION` | Verfassung (BV) |
| `INTERNATIONAL_TREATY` | Internationaler Vertrag |
| `ALL` | All types |

**`Language`** - Supported languages:
| Value | Language |
|-------|----------|
| `GERMAN` | German (de) |
| `FRENCH` | French (fr) |
| `ITALIAN` | Italian (it) |
| `ROMANSH` | Romansh (rm) |
| `ENGLISH` | English (en) |

#### Response Models

**`LawSearchResult`**
```python
class LawSearchResult(BaseModel):
   query: str                    # Original search query
   domain: LegalDomain           # Legal domain searched
   language: Language            # Language of results
   total_results: int            # Total number of results found
   results: list[LawEntry]       # List of matching laws
   search_timestamp: str         # ISO timestamp of the search
   suggestions: list[str]        # Related search suggestions
   notes: list[str]              # Additional notes
```

**`LawEntry`**
```python
class LawEntry(BaseModel):
   sr_number: str                # Systematic compilation number (e.g., "220")
   title: str                    # Official title of the law
   abbreviation: str | None      # Common abbreviation (e.g., "OR", "ZGB")
   law_type: str                 # Type of legal document
   enactment_date: date | None   # Date of enactment
   entry_into_force: date | None # Date law entered into force
   language: Language            # Language of this entry
   fedlex_url: str               # URL to full law on Fedlex
   relevant_articles: list[LawArticle]  # Matching articles
   summary: str | None           # Brief summary

   @property
   def full_citation(self) -> str  # e.g., "OR (SR 220)"
```

**`LawArticle`**
```python
class LawArticle(BaseModel):
   article_number: str           # e.g., "Art. 8", "Art. 261bis"
   title: str | None             # Article title if available
   content: str                  # Full text content
   paragraph: str | None         # Specific paragraph if applicable
```

#### Helper Functions

```python
def get_law_by_sr_number(
   sr_number: str,                      # SR number (e.g., "220")
   language: Language = Language.GERMAN
) -> LawEntry | None

def get_common_law_abbreviations() -> dict[str, str]
# Returns: {"OR": "220", "ZGB": "210", "StGB": "311.0", ...}
```

#### Common Swiss Law Abbreviations

| Abbreviation | SR Number | Full Name |
|--------------|-----------|-----------|
| **OR** | 220 | Obligationenrecht (Code of Obligations) |
| **ZGB** | 210 | Zivilgesetzbuch (Civil Code) |
| **StGB** | 311.0 | Strafgesetzbuch (Criminal Code) |
| **ZPO** | 272 | Zivilprozessordnung (Civil Procedure Code) |
| **StPO** | 312.0 | Strafprozessordnung (Criminal Procedure Code) |
| **BV** | 101 | Bundesverfassung (Federal Constitution) |
| **BGG** | 173.110 | Bundesgerichtsgesetz (Federal Court Act) |
| **SchKG** | 281.1 | Schuldbetreibungs- und Konkursgesetz (Debt Collection) |
| **ArG** | 822.11 | Arbeitsgesetz (Labor Act) |
| **KVG** | 832.10 | Krankenversicherungsgesetz (Health Insurance Act) |
| **DSG** | 235.1 | Datenschutzgesetz (Data Protection Act) |
| **AHVG** | 831.10 | AHV-Gesetz (Old-Age Insurance) |
| **BVG** | 831.40 | Berufliche Vorsorge (Occupational Pensions) |

#### Usage Examples

**Basic keyword search:**
```python
from legal_support.tools import search_laws, LegalDomain, Language

# Search for contract-related laws
result = search_laws("Arbeitsvertrag")
for law in result.results:
   print(f"{law.abbreviation}: {law.title}")
   print(f"  URL: {law.fedlex_url}")
```

**Search by abbreviation:**
```python
result = search_laws("OR")
law = result.results[0]
print(law.full_citation)  # "OR (SR 220)"
```

**Domain-specific search:**
```python
result = search_laws(
   query="Haftung",
   domain=LegalDomain.PRIVATE_LAW,
   language=Language.GERMAN,
   limit=5,
)
```

**Async search:**
```python
import asyncio
from legal_support.tools import search_laws_async

async def find_laws():
   result = await search_laws_async(
       query="Datenschutz",
       domain=LegalDomain.ALL,
       use_mock=False,  # Use live Fedlex API
   )
   return result

result = asyncio.run(find_laws())
```

**Direct SR lookup:**
```python
from legal_support.tools import get_law_by_sr_number

or_law = get_law_by_sr_number("220")
print(or_law.title)  # Obligationenrecht
print(or_law.fedlex_url)  # https://www.fedlex.admin.ch/eli/cc/220/de
```

#### Data Sources

- **Primary:** [Fedlex SPARQL Endpoint](https://fedlex.data.admin.ch/sparql) - Official Swiss federal law database
- **Web Interface:** [fedlex.admin.ch](https://www.fedlex.admin.ch) - Official publication platform
- **Fallback:** Local mock database with common Swiss laws for offline/testing use

#### Error Handling

```python
from legal_support.tools import search_laws, FedlexAPIError

try:
   result = search_laws("contract")
except FedlexAPIError as e:
   print(f"API Error: {e.message} (Status: {e.status_code})")
except ValueError as e:
   print(f"Invalid input: {e}")
```

#### Notes

- Results default to German (`de`) as it's the most commonly used language for Swiss federal law
- The tool supports all four Swiss national languages plus English
- For authoritative legal text, always consult the official version at fedlex.admin.ch
- Mock data is used by default for reliability; set `use_mock=False` for live API queries
