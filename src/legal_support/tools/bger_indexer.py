"""
BGER (Swiss Federal Court) Data Indexer for Vector Database.

This module provides functionality to:
1. Load BGER decisions from various sources (JSON, CSV, API)
2. Generate embeddings using sentence transformers
3. Build FAISS indexes for semantic search
4. Upload indexes to Hugging Face Hub for sharing

Usage:
    # Build index from local data
    python -m legal_support.tools.bger_indexer build --input data/bger_cases.json

    # Build and upload to Hugging Face Hub
    python -m legal_support.tools.bger_indexer build --input data/bger_cases.json --upload

For open-source distribution, the recommended workflow is:
1. Prepare data in standard JSON format
2. Build the index locally
3. Upload to Hugging Face Hub as a dataset
4. Users can then download automatically via the semantic_case_search tool
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Constants
DEFAULT_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
DEFAULT_OUTPUT_DIR = Path(__file__).parent.parent.parent.parent / "data" / "vector_index"
BATCH_SIZE = 32


@dataclass
class BGERCase:
    """Represents a BGER (Swiss Federal Court) decision."""

    case_id: str  # e.g., "BGE 147 III 451" or "4A_123/2021"
    title: str
    legal_area: str
    text_for_embedding: str  # Combined text for embedding generation
    chamber: str | None = None
    decision_date: date | None = None
    language: str = "de"
    regeste: str | None = None
    keywords: list[str] = field(default_factory=list)
    cited_laws: list[str] = field(default_factory=list)
    bger_url: str | None = None
    full_text: str | None = None

    def to_metadata(self) -> dict[str, Any]:
        """Convert to metadata dict for storage."""
        return {
            "case_id": self.case_id,
            "title": self.title,
            "legal_area": self.legal_area,
            "chamber": self.chamber,
            "decision_date": self.decision_date.isoformat() if self.decision_date else None,
            "language": self.language,
            "regeste": self.regeste,
            "keywords": self.keywords,
            "cited_laws": self.cited_laws,
            "bger_url": self.bger_url,
        }


class BGERDataLoader:
    """
    Load BGER case data from various sources.

    Supports:
    - JSON files (recommended format)
    - CSV files
    - JSONL files (one case per line)
    """

    @staticmethod
    def load_json(path: Path) -> list[BGERCase]:
        """Load cases from a JSON file."""
        logger.info(f"Loading cases from {path}")
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        cases = []
        items = data if isinstance(data, list) else data.get("cases", [])

        for item in items:
            case = BGERDataLoader._parse_case(item)
            if case:
                cases.append(case)

        logger.info(f"Loaded {len(cases)} cases from {path}")
        return cases

    @staticmethod
    def load_jsonl(path: Path) -> list[BGERCase]:
        """Load cases from a JSONL file (one JSON object per line)."""
        logger.info(f"Loading cases from {path}")
        cases = []

        with path.open("r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                    case = BGERDataLoader._parse_case(item)
                    if case:
                        cases.append(case)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse line {line_num}: {e}")

        logger.info(f"Loaded {len(cases)} cases from {path}")
        return cases

    @staticmethod
    def load_csv(path: Path) -> list[BGERCase]:
        """Load cases from a CSV file."""
        import csv

        logger.info(f"Loading cases from {path}")
        cases = []

        with path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                case = BGERDataLoader._parse_case(row)
                if case:
                    cases.append(case)

        logger.info(f"Loaded {len(cases)} cases from {path}")
        return cases

    @staticmethod
    def _parse_case(item: dict[str, Any]) -> BGERCase | None:
        """Parse a case from a dictionary."""
        # Required fields
        case_id = item.get("case_id") or item.get("id") or item.get("reference")
        if not case_id:
            return None

        title = item.get("title") or item.get("summary") or ""
        legal_area = item.get("legal_area") or item.get("domain") or "unknown"

        # Text for embedding - combine available text fields
        text_parts = []
        if title:
            text_parts.append(title)
        if item.get("regeste"):
            text_parts.append(item["regeste"])
        if item.get("keywords"):
            keywords = item["keywords"]
            if isinstance(keywords, list):
                text_parts.append(" ".join(keywords))
            else:
                text_parts.append(str(keywords))
        if item.get("full_text"):
            # Limit full text to avoid very long embeddings
            full_text = str(item["full_text"])[:5000]
            text_parts.append(full_text)

        text_for_embedding = " ".join(text_parts) if text_parts else title

        # Optional fields
        decision_date = None
        if item.get("decision_date"):
            try:
                date_str = str(item["decision_date"])
                if "T" in date_str:
                    decision_date = datetime.fromisoformat(date_str.split("T")[0]).date()
                else:
                    decision_date = date.fromisoformat(date_str)
            except (ValueError, TypeError):
                pass

        keywords = item.get("keywords", [])
        if isinstance(keywords, str):
            keywords = [k.strip() for k in keywords.split(",") if k.strip()]

        cited_laws = item.get("cited_laws", [])
        if isinstance(cited_laws, str):
            cited_laws = [l.strip() for l in cited_laws.split(",") if l.strip()]

        return BGERCase(
            case_id=str(case_id),
            title=title,
            legal_area=legal_area,
            text_for_embedding=text_for_embedding,
            chamber=item.get("chamber"),
            decision_date=decision_date,
            language=item.get("language", "de"),
            regeste=item.get("regeste"),
            keywords=keywords,
            cited_laws=cited_laws,
            bger_url=item.get("bger_url") or item.get("url"),
            full_text=item.get("full_text"),
        )

    @classmethod
    def load(cls, path: Path) -> list[BGERCase]:
        """Load cases from a file, auto-detecting format."""
        if not path.exists():
            msg = f"File not found: {path}"
            raise FileNotFoundError(msg)

        suffix = path.suffix.lower()
        if suffix == ".json":
            return cls.load_json(path)
        elif suffix == ".jsonl":
            return cls.load_jsonl(path)
        elif suffix == ".csv":
            return cls.load_csv(path)
        else:
            msg = f"Unsupported file format: {suffix}"
            raise ValueError(msg)


class BGERIndexBuilder:
    """
    Build FAISS vector index from BGER cases.

    This class handles:
    - Generating embeddings using sentence transformers
    - Building FAISS index for efficient similarity search
    - Saving index and metadata for later use
    """

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    ) -> None:
        """
        Initialize the index builder.

        Args:
            model_name: Sentence transformer model name. The default model
                       supports German, French, Italian, and English.
            output_dir: Directory to save the index and metadata.
        """
        self.model_name = model_name
        self.output_dir = Path(output_dir)
        self._model = None

    def _load_model(self):
        """Load the sentence transformer model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                logger.info(f"Loading model: {self.model_name}")
                self._model = SentenceTransformer(self.model_name)
            except ImportError:
                msg = (
                    "sentence-transformers is required. "
                    "Install with: pip install sentence-transformers"
                )
                raise ImportError(msg) from None
        return self._model

    def build_index(
        self,
        cases: list[BGERCase],
        version: str = "1.0.0",
        normalize: bool = True,
    ) -> tuple[Any, list[dict[str, Any]]]:
        """
        Build FAISS index from cases.

        Args:
            cases: List of BGERCase objects to index
            version: Version string for the index
            normalize: Whether to L2-normalize embeddings (recommended)

        Returns:
            Tuple of (faiss_index, metadata_list)
        """
        try:
            import faiss
            import numpy as np
        except ImportError:
            msg = "faiss-cpu and numpy are required. Install with: pip install faiss-cpu numpy"
            raise ImportError(msg) from None

        model = self._load_model()

        # Generate embeddings
        logger.info(f"Generating embeddings for {len(cases)} cases...")
        texts = [case.text_for_embedding for case in cases]

        embeddings = []
        for i in range(0, len(texts), BATCH_SIZE):
            batch = texts[i : i + BATCH_SIZE]
            batch_embeddings = model.encode(batch, convert_to_numpy=True, show_progress_bar=True)
            embeddings.append(batch_embeddings)
            logger.info(f"Processed {min(i + BATCH_SIZE, len(texts))}/{len(texts)} cases")

        embeddings_array = np.vstack(embeddings).astype(np.float32)

        # Normalize embeddings
        if normalize:
            logger.info("Normalizing embeddings...")
            faiss.normalize_L2(embeddings_array)

        # Build FAISS index
        logger.info("Building FAISS index...")
        dimension = embeddings_array.shape[1]
        index = faiss.IndexFlatIP(dimension)  # Inner product for normalized vectors
        index.add(embeddings_array)

        # Prepare metadata
        metadata = [case.to_metadata() for case in cases]

        logger.info(f"Built index with {index.ntotal} vectors of dimension {dimension}")

        return index, metadata

    def save_index(
        self,
        index: Any,
        metadata: list[dict[str, Any]],
        version: str = "1.0.0",
    ) -> Path:
        """
        Save FAISS index and metadata to disk.

        Args:
            index: FAISS index object
            metadata: List of case metadata dictionaries
            version: Version string for the index

        Returns:
            Path to the output directory
        """
        try:
            import faiss
        except ImportError:
            msg = "faiss-cpu is required. Install with: pip install faiss-cpu"
            raise ImportError(msg) from None

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Save FAISS index
        index_path = self.output_dir / "bger.index"
        logger.info(f"Saving FAISS index to {index_path}")
        faiss.write_index(index, str(index_path))

        # Save metadata
        metadata_path = self.output_dir / "bger_metadata.json"
        logger.info(f"Saving metadata to {metadata_path}")
        with metadata_path.open("w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        # Save version info
        version_path = self.output_dir / "version.json"
        version_info = {
            "version": version,
            "model_name": self.model_name,
            "num_cases": len(metadata),
            "created_at": datetime.now().isoformat(),
            "index_type": "IndexFlatIP",
        }
        with version_path.open("w", encoding="utf-8") as f:
            json.dump(version_info, f, indent=2)

        logger.info(f"Index saved to {self.output_dir}")
        return self.output_dir

    def upload_to_hub(
        self,
        repo_id: str,
        private: bool = False,
        token: str | None = None,
    ) -> str:
        """
        Upload the index to Hugging Face Hub.

        Args:
            repo_id: Hugging Face Hub repository ID (e.g., "username/bger-index")
            private: Whether to make the repository private
            token: Hugging Face API token (uses cached token if not provided)

        Returns:
            URL of the uploaded dataset
        """
        try:
            from huggingface_hub import HfApi, create_repo
        except ImportError:
            msg = "huggingface_hub is required. Install with: pip install huggingface_hub"
            raise ImportError(msg) from None

        api = HfApi(token=token)

        # Create the repository if it doesn't exist
        logger.info(f"Creating/updating repository: {repo_id}")
        create_repo(repo_id, repo_type="dataset", private=private, exist_ok=True, token=token)

        # Upload all index files
        files_to_upload = ["bger.index", "bger_metadata.json", "version.json"]

        for filename in files_to_upload:
            file_path = self.output_dir / filename
            if file_path.exists():
                logger.info(f"Uploading {filename}...")
                api.upload_file(
                    path_or_fileobj=str(file_path),
                    path_in_repo=filename,
                    repo_id=repo_id,
                    repo_type="dataset",
                    token=token,
                )

        # Create README
        readme_content = self._generate_readme(repo_id)
        readme_path = self.output_dir / "README.md"
        with readme_path.open("w", encoding="utf-8") as f:
            f.write(readme_content)

        api.upload_file(
            path_or_fileobj=str(readme_path),
            path_in_repo="README.md",
            repo_id=repo_id,
            repo_type="dataset",
            token=token,
        )

        url = f"https://huggingface.co/datasets/{repo_id}"
        logger.info(f"Index uploaded to {url}")
        return url

    def _generate_readme(self, repo_id: str) -> str:
        """Generate README content for the Hugging Face Hub dataset."""
        # Load version info
        version_path = self.output_dir / "version.json"
        version_info = {}
        if version_path.exists():
            with version_path.open("r") as f:
                version_info = json.load(f)

        return f"""---
license: cc-by-sa-4.0
language:
  - de
  - fr
  - it
tags:
  - legal
  - swiss-law
  - bger
  - vector-database
  - semantic-search
---

# BGER Semantic Search Index

This dataset contains a pre-built FAISS vector index for semantic search over
Swiss Federal Court (BGER) decisions.

## Contents

- `bger.index` - FAISS index file (IndexFlatIP)
- `bger_metadata.json` - Case metadata (case_id, title, legal_area, etc.)
- `version.json` - Index version and build information

## Usage

This index is designed to be used with the `legal-support` Python package:

```python
from legal_support.tools import semantic_case_search

# Search for similar cases
result = semantic_case_search("Arbeitsvertrag Kündigung fristlos")
for case in result.cases:
    print(f"{{case.case_id}}: {{case.similarity_score:.2f}}")
```

The index will be automatically downloaded on first use.

## Index Information

- **Model**: {version_info.get("model_name", "unknown")}
- **Number of cases**: {version_info.get("num_cases", "unknown")}
- **Version**: {version_info.get("version", "unknown")}
- **Created**: {version_info.get("created_at", "unknown")}

## License

The index structure and code are licensed under Apache 2.0.
The underlying BGER decision data is public domain (Swiss federal court decisions).

## Citation

If you use this dataset, please cite:

```bibtex
@misc{{bger-semantic-index,
  title={{BGER Semantic Search Index}},
  year={{2024}},
  publisher={{Hugging Face}},
  url={{https://huggingface.co/datasets/{repo_id}}}
}}
```
"""


def build_index_cli(
    input_path: str,
    output_dir: str | None = None,
    model_name: str = DEFAULT_MODEL,
    version: str = "1.0.0",
    upload: bool = False,
    repo_id: str | None = None,
    hf_token: str | None = None,
) -> None:
    """
    CLI function to build and optionally upload the vector index.

    Args:
        input_path: Path to input data file (JSON, JSONL, or CSV)
        output_dir: Directory to save the index (default: data/vector_index)
        model_name: Sentence transformer model name
        version: Version string for the index
        upload: Whether to upload to Hugging Face Hub
        repo_id: Hugging Face Hub repository ID (required if upload=True)
        hf_token: Hugging Face API token
    """
    import sys

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    # Load data
    input_path_obj = Path(input_path)
    try:
        cases = BGERDataLoader.load(input_path_obj)
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        sys.exit(1)

    if not cases:
        logger.error("No cases loaded from input file")
        sys.exit(1)

    # Build index
    output_dir_path = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
    builder = BGERIndexBuilder(model_name=model_name, output_dir=output_dir_path)

    try:
        index, metadata = builder.build_index(cases, version=version)
        builder.save_index(index, metadata, version=version)
    except Exception as e:
        logger.error(f"Failed to build index: {e}")
        sys.exit(1)

    # Upload to Hugging Face Hub
    if upload:
        if not repo_id:
            logger.error("--repo-id is required when uploading to Hugging Face Hub")
            sys.exit(1)
        try:
            url = builder.upload_to_hub(repo_id=repo_id, token=hf_token)
            logger.info(f"Successfully uploaded to {url}")
        except Exception as e:
            logger.error(f"Failed to upload to Hugging Face Hub: {e}")
            sys.exit(1)

    logger.info("Done!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build FAISS vector index from BGER case data")
    parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Path to input data file (JSON, JSONL, or CSV)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Output directory for the index",
    )
    parser.add_argument(
        "--model",
        "-m",
        default=DEFAULT_MODEL,
        help="Sentence transformer model name",
    )
    parser.add_argument(
        "--version",
        "-v",
        default="1.0.0",
        help="Version string for the index",
    )
    parser.add_argument(
        "--upload",
        action="store_true",
        help="Upload to Hugging Face Hub after building",
    )
    parser.add_argument(
        "--repo-id",
        help="Hugging Face Hub repository ID (required with --upload)",
    )
    parser.add_argument(
        "--hf-token",
        help="Hugging Face API token",
    )

    args = parser.parse_args()

    build_index_cli(
        input_path=args.input,
        output_dir=args.output,
        model_name=args.model,
        version=args.version,
        upload=args.upload,
        repo_id=args.repo_id,
        hf_token=args.hf_token,
    )
