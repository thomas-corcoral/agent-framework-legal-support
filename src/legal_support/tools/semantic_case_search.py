"""
Semantic Case Search Tool for Swiss Federal Court (BGER) Decisions.

This module provides semantic similarity search over Swiss Federal Court decisions
using vector embeddings and FAISS for efficient similarity search.

The vector database can be:
1. Downloaded from Hugging Face Hub (recommended for most users)
2. Built locally from BGER data using the provided scripts

Example usage:
    from legal_support.tools import semantic_case_search

    # Search for similar cases
    results = semantic_case_search("Mietvertrag Kündigung Zahlungsverzug")
    for case in results.cases:
        print(f"{case.case_id}: {case.title}")
        print(f"  Relevance: {case.similarity_score:.2f}")
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, date
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    import numpy as np
    import numpy.typing as npt

logger = logging.getLogger(__name__)

# Default paths for vector database
DEFAULT_INDEX_DIR = Path(__file__).parent.parent.parent.parent / "data" / "vector_index"
HF_REPO_ID = "swiss-legal/bger-semantic-index"  # Placeholder - will be created


class LegalArea(str, Enum):
    """Swiss Federal Court legal areas (Rechtsgebiete)."""

    CIVIL = "civil"  # Zivilrecht
    CRIMINAL = "criminal"  # Strafrecht
    PUBLIC = "public"  # Öffentliches Recht
    SOCIAL_INSURANCE = "social_insurance"  # Sozialversicherungsrecht
    ADMINISTRATIVE = "administrative"  # Verwaltungsrecht
    TAX = "tax"  # Steuerrecht
    ALL = "all"


class CourtChamber(str, Enum):
    """Swiss Federal Court chambers (Abteilungen)."""

    FIRST_CIVIL = "I_civil"  # I. zivilrechtliche Abteilung
    SECOND_CIVIL = "II_civil"  # II. zivilrechtliche Abteilung
    CRIMINAL = "criminal"  # Strafrechtliche Abteilung
    FIRST_PUBLIC = "I_public"  # I. öffentlich-rechtliche Abteilung
    SECOND_PUBLIC = "II_public"  # II. öffentlich-rechtliche Abteilung
    THIRD_PUBLIC = "III_public"  # III. öffentlich-rechtliche Abteilung (until 2006)
    SOCIAL_INSURANCE = "social"  # Sozialrechtliche Abteilungen
    ALL = "all"


class CaseDecision(BaseModel):
    """A Swiss Federal Court decision with metadata."""

    case_id: str = Field(description="BGE/BGer reference number (e.g., 'BGE 147 III 451')")
    title: str = Field(description="Title or summary of the decision")
    legal_area: str = Field(description="Primary legal area")
    chamber: str | None = Field(default=None, description="Court chamber")
    decision_date: date | None = Field(default=None, description="Date of decision")
    language: str = Field(default="de", description="Language of the decision")
    regeste: str | None = Field(default=None, description="Regeste (headnote/summary)")
    keywords: list[str] = Field(default_factory=list, description="Legal keywords")
    cited_laws: list[str] = Field(default_factory=list, description="Laws cited in decision")
    bger_url: str | None = Field(default=None, description="URL to full decision on bger.ch")
    similarity_score: float = Field(default=0.0, description="Semantic similarity score (0-1)")

    @property
    def full_citation(self) -> str:
        """Return full citation string."""
        return f"{self.case_id} ({self.decision_date})" if self.decision_date else self.case_id


class CaseSearchResult(BaseModel):
    """Result of a semantic case search."""

    query: str = Field(description="Original search query")
    legal_area: LegalArea = Field(description="Legal area filter applied")
    total_results: int = Field(description="Total number of matching cases")
    cases: list[CaseDecision] = Field(description="List of matching cases")
    search_timestamp: str = Field(description="ISO timestamp of the search")
    index_version: str = Field(default="", description="Version of the vector index used")
    notes: list[str] = Field(default_factory=list, description="Additional search notes")


class VectorIndex:
    """
    Vector index for semantic case search using FAISS.

    This class manages the embedding model and FAISS index for
    efficient semantic similarity search over court decisions.
    """

    def __init__(
        self,
        index_dir: Path | str | None = None,
        model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    ) -> None:
        """
        Initialize the vector index.

        Args:
            index_dir: Directory containing the FAISS index and metadata.
                      If None, uses default location or downloads from HF Hub.
            model_name: Sentence transformer model for embeddings.
                       Default uses multilingual model for DE/FR/IT support.
        """
        self.index_dir = Path(index_dir) if index_dir else DEFAULT_INDEX_DIR
        self.model_name = model_name
        self._index: object | None = None
        self._metadata: list[dict[str, object]] = []
        self._model: object | None = None
        self._index_version: str = ""

    def _ensure_loaded(self) -> None:
        """Ensure the index and model are loaded."""
        if self._index is None:
            self._load_or_download_index()
        if self._model is None:
            self._load_model()

    def _load_model(self) -> None:
        """Load the sentence transformer model."""
        try:
            from sentence_transformers import SentenceTransformer

            logger.info(f"Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
        except ImportError:
            msg = (
                "sentence-transformers is required for semantic search. "
                "Install with: pip install legal-support[vector]"
            )
            raise ImportError(msg) from None

    def _load_or_download_index(self) -> None:
        """Load local index or download from Hugging Face Hub."""
        index_path = self.index_dir / "bger.index"
        metadata_path = self.index_dir / "bger_metadata.json"
        version_path = self.index_dir / "version.json"

        if index_path.exists() and metadata_path.exists():
            self._load_local_index(index_path, metadata_path, version_path)
        else:
            logger.info("Local index not found, attempting to download from Hugging Face Hub...")
            self._download_from_hub()

    def _load_local_index(
        self, index_path: Path, metadata_path: Path, version_path: Path | None = None
    ) -> None:
        """Load FAISS index and metadata from local files."""
        try:
            import faiss

            logger.info(f"Loading FAISS index from {index_path}")
            self._index = faiss.read_index(str(index_path))

            logger.info(f"Loading metadata from {metadata_path}")
            with metadata_path.open("r", encoding="utf-8") as f:
                self._metadata = json.load(f)

            if version_path and version_path.exists():
                with version_path.open("r", encoding="utf-8") as f:
                    version_info = json.load(f)
                    self._index_version = version_info.get("version", "unknown")

            logger.info(
                f"Loaded index with {len(self._metadata)} cases (version: {self._index_version})"
            )

        except ImportError:
            msg = (
                "faiss-cpu is required for semantic search. "
                "Install with: pip install legal-support[vector]"
            )
            raise ImportError(msg) from None

    def _download_from_hub(self) -> None:
        """Download the vector index from Hugging Face Hub."""
        try:
            from huggingface_hub import hf_hub_download

            logger.info(f"Downloading BGER index from {HF_REPO_ID}...")

            # Create index directory
            self.index_dir.mkdir(parents=True, exist_ok=True)

            # Download files
            for filename in ["bger.index", "bger_metadata.json", "version.json"]:
                local_path = hf_hub_download(
                    repo_id=HF_REPO_ID,
                    filename=filename,
                    local_dir=self.index_dir,
                    repo_type="dataset",
                )
                logger.info(f"Downloaded {filename} to {local_path}")

            # Load the downloaded index
            self._load_local_index(
                self.index_dir / "bger.index",
                self.index_dir / "bger_metadata.json",
                self.index_dir / "version.json",
            )

        except ImportError:
            msg = (
                "huggingface_hub is required to download the index. "
                "Install with: pip install legal-support[vector]"
            )
            raise ImportError(msg) from None
        except Exception as e:
            msg = (
                f"Failed to download index from Hugging Face Hub: {e}. "
                "You can build the index locally with: legal-support build-index"
            )
            raise RuntimeError(msg) from e

    def embed_query(self, query: str) -> npt.NDArray[np.float32]:
        """Generate embedding for a query string."""
        self._ensure_loaded()
        if self._model is None:
            msg = "Model not loaded"
            raise RuntimeError(msg)
        return self._model.encode([query], convert_to_numpy=True)[0]

    def search(
        self,
        query: str,
        k: int = 10,
        legal_area: LegalArea = LegalArea.ALL,
        min_date: date | None = None,
        max_date: date | None = None,
    ) -> list[tuple[dict[str, object], float]]:
        """
        Search for similar cases.

        Args:
            query: Search query text
            k: Number of results to return
            legal_area: Filter by legal area
            min_date: Filter by minimum decision date
            max_date: Filter by maximum decision date

        Returns:
            List of (metadata, similarity_score) tuples
        """
        self._ensure_loaded()

        # Generate query embedding
        query_embedding = self.embed_query(query)

        # Search FAISS index
        import numpy as np

        query_vector = np.array([query_embedding], dtype=np.float32)

        # Get more results than k to allow for filtering
        search_k = min(k * 3, len(self._metadata))
        distances, indices = self._index.search(query_vector, search_k)

        # Convert distances to similarity scores (FAISS returns L2 distances)
        # For normalized vectors, similarity = 1 - distance/2
        similarities = 1 - distances[0] / 2

        # Filter and collect results
        results: list[tuple[dict[str, object], float]] = []
        for idx, sim in zip(indices[0], similarities, strict=False):
            if idx < 0 or idx >= len(self._metadata):
                continue

            metadata = self._metadata[idx]

            # Apply filters
            if legal_area != LegalArea.ALL:
                if metadata.get("legal_area") != legal_area.value:
                    continue

            if min_date or max_date:
                case_date_str = metadata.get("decision_date")
                if case_date_str:
                    case_date = date.fromisoformat(case_date_str)
                    if min_date and case_date < min_date:
                        continue
                    if max_date and case_date > max_date:
                        continue

            results.append((metadata, float(sim)))

            if len(results) >= k:
                break

        return results

    @property
    def index_version(self) -> str:
        """Return the version of the loaded index."""
        return self._index_version


# Global index instance (lazy loaded)
_global_index: VectorIndex | None = None


def get_index(index_dir: Path | str | None = None) -> VectorIndex:
    """Get or create the global vector index instance."""
    global _global_index
    if _global_index is None:
        _global_index = VectorIndex(index_dir=index_dir)
    return _global_index


def semantic_case_search(
    query: str,
    legal_area: LegalArea = LegalArea.ALL,
    limit: int = 10,
    min_date: date | None = None,
    max_date: date | None = None,
    index_dir: Path | str | None = None,
) -> CaseSearchResult:
    """
    Search Swiss Federal Court decisions using semantic similarity.

    This function performs semantic search over BGER (Swiss Federal Court)
    decisions using pre-computed embeddings and FAISS similarity search.

    Args:
        query: Natural language search query. Can be in German, French,
               Italian, or English. Examples:
               - "Kündigung Mietvertrag Zahlungsverzug"
               - "résiliation du bail pour défaut de paiement"
               - "employment contract termination notice period"
        legal_area: Filter by legal domain (civil, criminal, public, etc.)
        limit: Maximum number of results to return (1-50)
        min_date: Only return cases decided after this date
        max_date: Only return cases decided before this date
        index_dir: Custom path to vector index directory

    Returns:
        CaseSearchResult with matching cases sorted by relevance

    Raises:
        ImportError: If required dependencies are not installed
        RuntimeError: If the index cannot be loaded or downloaded

    Example:
        >>> from legal_support.tools import semantic_case_search, LegalArea
        >>> result = semantic_case_search(
        ...     query="Arbeitsvertrag Kündigung fristlos", legal_area=LegalArea.CIVIL, limit=5
        ... )
        >>> for case in result.cases:
        ...     print(f"{case.case_id}: {case.similarity_score:.2f}")
    """
    from datetime import datetime

    # Validate parameters
    if not query or not query.strip():
        msg = "Query cannot be empty"
        raise ValueError(msg)
    limit = max(1, min(50, limit))

    # Get the vector index
    index = get_index(index_dir)

    # Perform search
    results = index.search(
        query=query.strip(),
        k=limit,
        legal_area=legal_area,
        min_date=min_date,
        max_date=max_date,
    )

    # Convert to CaseDecision objects
    cases = []
    for metadata, score in results:
        decision_date = None
        if metadata.get("decision_date"):
            decision_date = date.fromisoformat(str(metadata["decision_date"]))

        case = CaseDecision(
            case_id=str(metadata.get("case_id", "")),
            title=str(metadata.get("title", "")),
            legal_area=str(metadata.get("legal_area", "")),
            chamber=metadata.get("chamber"),
            decision_date=decision_date,
            language=str(metadata.get("language", "de")),
            regeste=metadata.get("regeste"),
            keywords=list(metadata.get("keywords", [])),
            cited_laws=list(metadata.get("cited_laws", [])),
            bger_url=metadata.get("bger_url"),
            similarity_score=score,
        )
        cases.append(case)

    return CaseSearchResult(
        query=query,
        legal_area=legal_area,
        total_results=len(cases),
        cases=cases,
        search_timestamp=datetime.now(UTC).isoformat(),
        index_version=index.index_version,
        notes=[
            "Results ranked by semantic similarity",
            "For authoritative text, visit bger.ch",
        ],
    )


async def semantic_case_search_async(
    query: str,
    legal_area: LegalArea = LegalArea.ALL,
    limit: int = 10,
    min_date: date | None = None,
    max_date: date | None = None,
    index_dir: Path | str | None = None,
) -> CaseSearchResult:
    """
    Async version of semantic_case_search.

    See semantic_case_search for full documentation.
    """
    import asyncio

    # Run the synchronous search in a thread pool
    return await asyncio.get_event_loop().run_in_executor(
        None,
        lambda: semantic_case_search(
            query=query,
            legal_area=legal_area,
            limit=limit,
            min_date=min_date,
            max_date=max_date,
            index_dir=index_dir,
        ),
    )
