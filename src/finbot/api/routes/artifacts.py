"""Artifact viewer — browse, preview, download, and delete imported files."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from finbot.api.deps import CurrentUser
from finbot.config import settings
from finbot.parsers import detect_and_parse
from finbot.parsers.tax_parser import TaxDocParser

router = APIRouter(prefix="/api/artifacts", tags=["artifacts"])


def _file_info(p: Path) -> dict:
    stat = p.stat()
    suffix = p.suffix.lower().lstrip(".")
    return {
        "filename": p.name,
        "type": suffix if suffix in ("pdf", "csv", "tsv", "ofx", "qfx") else "other",
        "size": stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
    }


@router.get("")
def list_artifacts(_user: CurrentUser):
    """List all files in data/imports/."""
    d = settings.imports_dir
    if not d.exists():
        return []
    files = sorted(
        (f for f in d.iterdir() if f.is_file() and not f.name.startswith(".")),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )
    return [_file_info(f) for f in files]


@router.get("/stats")
def artifact_stats(_user: CurrentUser):
    """Total file count, total size, oldest/newest dates."""
    d = settings.imports_dir
    if not d.exists():
        return {"count": 0, "total_size": 0, "oldest": None, "newest": None}

    files = [f for f in d.iterdir() if f.is_file() and not f.name.startswith(".")]
    if not files:
        return {"count": 0, "total_size": 0, "oldest": None, "newest": None}

    total = sum(f.stat().st_size for f in files)
    times = [f.stat().st_mtime for f in files]
    return {
        "count": len(files),
        "total_size": total,
        "oldest": datetime.fromtimestamp(min(times)).strftime("%Y-%m-%d %H:%M"),
        "newest": datetime.fromtimestamp(max(times)).strftime("%Y-%m-%d %H:%M"),
    }


@router.get("/{filename}")
def download_artifact(filename: str, _user: CurrentUser):
    """Download a specific file."""
    path = settings.imports_dir / filename
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, filename=filename)


@router.get("/{filename}/preview")
def preview_artifact(filename: str, _user: CurrentUser):
    """Re-parse the file and return a preview without importing."""
    path = settings.imports_dir / filename
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    suffix = path.suffix.lower()

    if suffix == ".pdf":
        tax_parser = TaxDocParser()
        tax_result = tax_parser.parse(path)
        if tax_result.doc_type != "other" and tax_result.confidence > 0.4:
            return {
                "preview_type": "tax",
                "doc_type": tax_result.doc_type,
                "tax_year": tax_result.tax_year,
                "confidence": tax_result.confidence,
                "fields": tax_result.fields,
                "warnings": tax_result.warnings,
            }

    result = detect_and_parse(path)
    txs = result.transactions[:20]
    return {
        "preview_type": "statement",
        "institution": result.account_institution,
        "transaction_count": len(result.transactions),
        "holding_count": len(result.holdings),
        "date_range": [str(result.date_range[0]), str(result.date_range[1])] if result.date_range else None,
        "total_debits": result.total_debits,
        "total_credits": result.total_credits,
        "transactions": [{"date": str(t.date), "amount": t.amount, "description": t.description} for t in txs],
        "warnings": result.warnings,
    }


@router.delete("/{filename}")
def delete_artifact(filename: str, _user: CurrentUser):
    """Delete a stored file."""
    path = settings.imports_dir / filename
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    path.unlink()
    return {"status": "deleted", "filename": filename}
