"""
Task 1: collect Vietnamese legal documents about drugs/prohibited substances.

The actual source files are stored in data/landing/legal/. This script keeps the
task reproducible by validating and summarizing the files already collected.
"""

from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"
VALID_EXTENSIONS = {".pdf", ".docx", ".doc"}
MIN_REQUIRED_FILES = 3


def setup_directory() -> None:
    """Create data/landing/legal/ if it does not exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Directory ready: {DATA_DIR}")


def list_legal_documents() -> list[dict]:
    """Return metadata for collected legal documents."""
    setup_directory()
    documents: list[dict] = []

    for path in sorted(DATA_DIR.iterdir()):
        if not path.is_file() or path.name.startswith("."):
            continue
        if path.suffix.lower() not in VALID_EXTENSIONS:
            continue

        documents.append(
            {
                "filename": path.name,
                "path": str(path),
                "extension": path.suffix.lower(),
                "size_bytes": path.stat().st_size,
            }
        )

    return documents


def validate_collection(min_files: int = MIN_REQUIRED_FILES) -> bool:
    """Check that enough non-empty legal documents have been collected."""
    documents = list_legal_documents()
    valid_documents = [doc for doc in documents if doc["size_bytes"] > 1024]

    print(f"Found {len(valid_documents)} legal documents:")
    for doc in valid_documents:
        size_kb = doc["size_bytes"] / 1024
        print(f"  - {doc['filename']} ({size_kb:.1f} KB)")

    if len(valid_documents) < min_files:
        print(f"Need at least {min_files} valid legal files.")
        return False

    print("Task 1 data is ready.")
    return True


if __name__ == "__main__":
    validate_collection()
