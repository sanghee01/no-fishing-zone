"""
Pydantic models for API request/response schemas.
"""

from typing import List, Literal
from pydantic import BaseModel, HttpUrl, Field


class AnalyzeRequest(BaseModel):
    """Request model for URL analysis endpoint."""
    url: str = Field(..., description="URL to analyze")
    request_id: str = Field(..., description="Unique request identifier")


class AnalyzeResponse(BaseModel):
    """Response model for URL analysis endpoint."""
    url: str = Field(..., description="Analyzed URL")
    status: Literal["SAFE", "WARNING", "BLOCK"] = Field(..., description="Risk status")
    risk_score: int = Field(..., ge=0, description="Total risk score")
    category: str = Field(default="", description="Content category (Common/Negative)")
    keyword: str = Field(default="", description="Detected brand/keyword")
    reasons: List[str] = Field(default_factory=list, description="Scoring reasons")


class AIAnalysisResult(BaseModel):
    """Result model from Claude AI analysis."""
    keyword: str = Field(default="", description="Detected brand name")
    risk_score: float = Field(default=0.0, ge=0.0, le=1.0, description="AI risk assessment (0.0~1.0)")
    category: Literal["Common", "Negative"] = Field(default="Common", description="Content category")
    description: str = Field(default="", description="Risk description")


class PhaseResult(BaseModel):
    """Result model for each analysis phase."""
    phase: str = Field(..., description="Phase name")
    score: int = Field(default=0, description="Score from this phase")
    reasons: List[str] = Field(default_factory=list, description="Reasons for scoring")
    should_block: bool = Field(default=False, description="Immediate block flag")
    skip_remaining: bool = Field(default=False, description="Skip remaining phases flag")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")
