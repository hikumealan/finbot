"""User guide endpoints."""
from fastapi import APIRouter, Query

from finbot.api.deps import CurrentUser
from finbot.api.schemas import GuideSection, SearchResult
from finbot.guide.content import GUIDE_SECTIONS, search_guide

router = APIRouter(prefix="/api/guide", tags=["guide"])


@router.get("/sections", response_model=list[GuideSection])
def get_sections(_user: CurrentUser):
    return [GuideSection(title=s["title"], content=s["content"]) for s in GUIDE_SECTIONS]


@router.get("/search", response_model=list[SearchResult])
def search(q: str = Query(..., min_length=2), _user: CurrentUser = None):
    results = search_guide(q)
    return [SearchResult(title=t, snippet=s) for t, s in results]
