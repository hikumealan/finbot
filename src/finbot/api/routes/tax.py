"""Tax analysis and document upload endpoints."""
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile
from pydantic import BaseModel

from finbot.analysis.tax_optimizer import compute_tax_position, find_tlh_candidates
from finbot.api.deps import CurrentUser, DbSession
from finbot.api.schemas import TaxPositionOut, TLHCandidateOut
from finbot.config import settings
from finbot.models.tax_document import TaxDocument, TaxLineItem
from finbot.models.user_profile import UserProfile
from finbot.parsers.tax_parser import TaxDocParser
from finbot.security.audit import create_audit_entry

router = APIRouter(prefix="/api/tax", tags=["tax"])


@router.get("/position", response_model=TaxPositionOut)
def get_position(db: DbSession, _user: CurrentUser, year: int = 2025):
    profile = db.query(UserProfile).first()
    filing = profile.filing_status if profile else "single"
    state = profile.state_of_residence if profile else None
    pos = compute_tax_position(db, filing, state, year)
    return TaxPositionOut(**pos.__dict__)


@router.get("/tlh", response_model=list[TLHCandidateOut])
def get_tlh(db: DbSession, _user: CurrentUser):
    return [TLHCandidateOut(**c.__dict__) for c in find_tlh_candidates(db)]


@router.post("/upload")
async def upload_tax_doc(file: UploadFile, db: DbSession, _user: CurrentUser):
    content = await file.read()
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(content)
        tmp_path = Path(f.name)

    try:
        parser = TaxDocParser()
        result = parser.parse(tmp_path)

        import shutil
        from datetime import datetime

        settings.ensure_dirs()
        stored_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename or 'tax.pdf'}"
        shutil.copy2(tmp_path, settings.imports_dir / stored_name)

        doc = TaxDocument(tax_year=result.tax_year or 0, doc_type=result.doc_type, source_file=file.filename)
        db.add(doc)
        db.flush()

        for key, value in result.fields.items():
            db.add(TaxLineItem(
                tax_document_id=doc.id, field_key=key,
                field_label=key.replace("_", " ").title(), value=value,
            ))

        create_audit_entry(db, "import", "tax_document", doc.id, {"file": file.filename, "doc_type": result.doc_type})
        db.commit()

        return {"id": doc.id, "doc_type": result.doc_type, "tax_year": result.tax_year, "fields": len(result.fields), "confidence": result.confidence, "warnings": result.warnings}
    finally:
        tmp_path.unlink(missing_ok=True)


@router.get("/documents")
def list_documents(db: DbSession, _user: CurrentUser):
    docs = db.query(TaxDocument).order_by(TaxDocument.tax_year.desc()).all()
    return [{"id": d.id, "tax_year": d.tax_year, "doc_type": d.doc_type, "source_file": d.source_file, "imported_at": str(d.imported_at)[:19]} for d in docs]


@router.get("/documents/{doc_id}/fields")
def get_document_fields(doc_id: int, db: DbSession, _user: CurrentUser):
    doc = db.query(TaxDocument).get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    items = db.query(TaxLineItem).filter_by(tax_document_id=doc_id).all()
    return [{"id": li.id, "field_key": li.field_key, "field_label": li.field_label, "value": li.value, "data_type": li.data_type} for li in items]


class FieldUpdate(BaseModel):
    value: str


@router.patch("/documents/{doc_id}/fields/{field_id}")
def update_field(doc_id: int, field_id: int, body: FieldUpdate, db: DbSession, _user: CurrentUser):
    li = db.query(TaxLineItem).filter_by(id=field_id, tax_document_id=doc_id).first()
    if not li:
        raise HTTPException(status_code=404, detail="Field not found")
    li.value = body.value
    create_audit_entry(db, "edit", "tax_line_item", field_id, {"field_key": li.field_key, "new_value": body.value})
    db.commit()
    return {"status": "updated"}


@router.delete("/documents/{doc_id}")
def delete_document(doc_id: int, db: DbSession, _user: CurrentUser):
    doc = db.query(TaxDocument).get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    db.query(TaxLineItem).filter_by(tax_document_id=doc_id).delete()
    db.delete(doc)
    create_audit_entry(db, "delete", "tax_document", doc_id)
    db.commit()
    return {"status": "deleted"}
