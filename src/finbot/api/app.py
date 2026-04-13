"""FastAPI application factory."""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from finbot.db.database import init_db
from finbot.db.seed import seed_all


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    from finbot.db.database import get_session

    with get_session() as session:
        seed_all(session)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="FinBot API",
        description="Local offline LLM-powered financial analyst",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from finbot.api.auth import router as auth_router
    from finbot.api.routes.accounts import router as accounts_router
    from finbot.api.routes.artifacts import router as artifacts_router
    from finbot.api.routes.backup import router as backup_router
    from finbot.api.routes.budgets import router as budgets_router
    from finbot.api.routes.chat import router as chat_router
    from finbot.api.routes.config import router as config_router
    from finbot.api.routes.dashboard import router as dashboard_router
    from finbot.api.routes.db_viewer import router as db_viewer_router
    from finbot.api.routes.debts import router as debts_router
    from finbot.api.routes.expenses import router as expenses_router
    from finbot.api.routes.export import router as export_router
    from finbot.api.routes.goals import router as goals_router
    from finbot.api.routes.guide import router as guide_router
    from finbot.api.routes.imports import router as imports_router
    from finbot.api.routes.investments import router as investments_router
    from finbot.api.routes.munis import router as munis_router
    from finbot.api.routes.paycheck import router as paycheck_router
    from finbot.api.routes.projections import router as projections_router
    from finbot.api.routes.search import router as search_router
    from finbot.api.routes.settings import router as settings_router
    from finbot.api.routes.snapshots import router as snapshots_router
    from finbot.api.routes.social_security import router as ss_router
    from finbot.api.routes.tax import router as tax_router
    from finbot.api.routes.transactions import router as transactions_router

    app.include_router(auth_router)
    app.include_router(dashboard_router)
    app.include_router(expenses_router)
    app.include_router(transactions_router)
    app.include_router(budgets_router)
    app.include_router(accounts_router)
    app.include_router(investments_router)
    app.include_router(munis_router)
    app.include_router(debts_router)
    app.include_router(goals_router)
    app.include_router(projections_router)
    app.include_router(tax_router)
    app.include_router(chat_router)
    app.include_router(config_router)
    app.include_router(settings_router)
    app.include_router(imports_router)
    app.include_router(export_router)
    app.include_router(backup_router)
    app.include_router(guide_router)
    app.include_router(db_viewer_router)
    app.include_router(artifacts_router)
    app.include_router(search_router)
    app.include_router(ss_router)
    app.include_router(paycheck_router)
    app.include_router(snapshots_router)

    static_dir = Path(__file__).resolve().parents[3] / "frontend" / ".output" / "public"
    if static_dir.exists():
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

    return app
