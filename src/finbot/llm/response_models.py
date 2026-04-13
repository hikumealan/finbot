"""Pydantic models for structured LLM output validation."""
from __future__ import annotations

from pydantic import BaseModel


class TransactionCategory(BaseModel):
    description: str
    category: str
    subcategory: str | None = None
    confidence: float = 1.0


class AnomalyDetection(BaseModel):
    description: str
    amount: float
    reason: str
    severity: str  # low/medium/high


class ReportSection(BaseModel):
    title: str
    content: str


class StructuredReport(BaseModel):
    executive_summary: str
    sections: list[ReportSection]
    recommendations: list[str]


class AdvisorResponse(BaseModel):
    answer: str
    key_points: list[str] = []
    action_items: list[str] = []
    disclaimer: str = "This is informational guidance, not professional financial advice."
