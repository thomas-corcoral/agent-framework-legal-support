"""Command-line interface for Legal support agents."""

from __future__ import annotations

import argparse
import sys

from legal_support import __version__


def cmd_version(args: argparse.Namespace) -> int:
    """Print version information."""
    print(f"Legal Swiss support v{__version__}")
    return 0


def cmd_build_index(args: argparse.Namespace) -> int:
    """Build FAISS vector index from BGER case data."""
    from legal_support.tools.bger_indexer import build_index_cli

    build_index_cli(
        input_path=args.input,
        output_dir=args.output,
        model_name=args.model,
        version=args.index_version,
        upload=args.upload,
        repo_id=args.repo_id,
        hf_token=args.hf_token,
    )
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    """Perform semantic search over BGER cases."""
    from legal_support.tools.semantic_case_search import LegalArea, semantic_case_search

    try:
        legal_area = LegalArea(args.legal_area) if args.legal_area else LegalArea.ALL
    except ValueError:
        print(f"Invalid legal area: {args.legal_area}")
        print(f"Valid options: {[a.value for a in LegalArea]}")
        return 1

    try:
        result = semantic_case_search(
            query=args.query,
            legal_area=legal_area,
            limit=args.limit,
            index_dir=args.index_dir,
        )
    except ImportError as e:
        print(f"Error: {e}")
        print("\nTo use semantic search, install the vector dependencies:")
        print("  pip install legal-support[vector]")
        return 1
    except RuntimeError as e:
        print(f"Error: {e}")
        return 1

    print(f"\nSearch results for: {result.query}")
    print(f"Legal area: {result.legal_area.value}")
    print(f"Found {result.total_results} matching cases\n")

    for i, case in enumerate(result.cases, 1):
        print(f"{i}. {case.case_id}")
        print(f"   Title: {case.title}")
        print(f"   Relevance: {case.similarity_score:.2%}")
        print(f"   Legal area: {case.legal_area}")
        if case.decision_date:
            print(f"   Date: {case.decision_date}")
        if case.bger_url:
            print(f"   URL: {case.bger_url}")
        print()

    return 0


def cmd_download_index(args: argparse.Namespace) -> int:
    """Download the pre-built index from Hugging Face Hub."""
    from legal_support.tools.semantic_case_search import VectorIndex

    print("Downloading BGER index from Hugging Face Hub...")
    try:
        index = VectorIndex(index_dir=args.output)
        index._ensure_loaded()
        print(f"Index downloaded successfully to {index.index_dir}")
        print(f"Version: {index.index_version}")
        return 0
    except ImportError as e:
        print(f"Error: {e}")
        print("\nInstall required dependencies:")
        print("  pip install legal-support[vector]")
        return 1
    except RuntimeError as e:
        print(f"Error: {e}")
        return 1


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="legal-support",
        description="Swiss Legal Support Tools - CLI for legal research and analysis",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Build index command
    build_parser = subparsers.add_parser(
        "build-index",
        help="Build FAISS vector index from BGER case data",
        description="""
Build a FAISS vector index from BGER (Swiss Federal Court) case data.

The input file should be JSON, JSONL, or CSV format with fields:
- case_id: Case reference (required)
- title: Case title/summary
- legal_area: Legal domain (civil, criminal, public, etc.)
- regeste: Case headnote (recommended for good search quality)
- full_text: Full decision text (optional)
- decision_date: Date of decision
- keywords: Legal keywords
- cited_laws: Laws cited in the decision
""",
    )
    build_parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Path to input data file (JSON, JSONL, or CSV)",
    )
    build_parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Output directory for the index (default: data/vector_index)",
    )
    build_parser.add_argument(
        "--model",
        "-m",
        default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        help="Sentence transformer model name",
    )
    build_parser.add_argument(
        "--index-version",
        "-v",
        default="1.0.0",
        help="Version string for the index",
    )
    build_parser.add_argument(
        "--upload",
        action="store_true",
        help="Upload to Hugging Face Hub after building",
    )
    build_parser.add_argument(
        "--repo-id",
        help="Hugging Face Hub repository ID (e.g., 'your-username/bger-index')",
    )
    build_parser.add_argument(
        "--hf-token",
        help="Hugging Face API token (or set HF_TOKEN env var)",
    )
    build_parser.set_defaults(func=cmd_build_index)

    # Search command
    search_parser = subparsers.add_parser(
        "search",
        help="Semantic search over BGER cases",
        description="Search Swiss Federal Court decisions using natural language queries.",
    )
    search_parser.add_argument(
        "query",
        help="Search query (natural language)",
    )
    search_parser.add_argument(
        "--legal-area",
        "-a",
        choices=["civil", "criminal", "public", "social_insurance", "administrative", "tax", "all"],
        default="all",
        help="Filter by legal area",
    )
    search_parser.add_argument(
        "--limit",
        "-n",
        type=int,
        default=10,
        help="Maximum number of results (default: 10)",
    )
    search_parser.add_argument(
        "--index-dir",
        help="Path to vector index directory",
    )
    search_parser.set_defaults(func=cmd_search)

    # Download index command
    download_parser = subparsers.add_parser(
        "download-index",
        help="Download pre-built index from Hugging Face Hub",
        description="Download the pre-built BGER semantic search index from Hugging Face Hub.",
    )
    download_parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Output directory for the index",
    )
    download_parser.set_defaults(func=cmd_download_index)

    return parser


def main() -> int:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()

    if args.command is None:
        print(f"Legal Swiss support v{__version__}")
        print("\nUse --help for available commands.")
        print("\nQuick start:")
        print("  legal-support search 'Arbeitsvertrag Kündigung'  # Search cases")
        print("  legal-support build-index -i data.json           # Build index")
        print("  legal-support download-index                     # Download pre-built index")
        return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
