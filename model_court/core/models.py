"""
Data models for Model Court system.

All data structures are defined using Pydantic for validation and serialization.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from uuid import uuid4


def generate_id() -> str:
    """Generate a unique ID."""
    return str(uuid4())


class CaseInput(BaseModel):
    """Input case to be evaluated."""
    
    case_id: str = Field(default_factory=generate_id, description="Unique case identifier")
    text: str = Field(..., description="The case text to be evaluated")
    domain: str = Field(default="general", description="Domain of the case (e.g., fact_check, finance, law)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    timestamp: datetime = Field(default_factory=datetime.now, description="Case submission timestamp")


class Precedent(BaseModel):
    """Historical precedent from court_code."""
    
    precedent_id: str = Field(..., description="Precedent identifier")
    claim: str = Field(..., description="The historical claim")
    verdict: str = Field(..., description="Previous verdict")
    reasoning: str = Field(..., description="Reasoning for the verdict")
    similarity_score: float = Field(..., description="Similarity score to current claim (0-1)")
    timestamp: datetime = Field(..., description="When this precedent was established")
    valid_from: Optional[datetime] = Field(None, description="Validity start date")
    valid_until: Optional[datetime] = Field(None, description="Validity end date")
    
    def is_valid(self, check_date: Optional[datetime] = None) -> bool:
        """Check if precedent is currently valid."""
        check_date = check_date or datetime.now()
        if self.valid_from and check_date < self.valid_from:
            return False
        if self.valid_until and check_date > self.valid_until:
            return False
        return True


class Claim(BaseModel):
    """Individual claim extracted from a case."""
    
    claim_id: str = Field(default_factory=generate_id, description="Unique claim identifier")
    text: str = Field(..., description="The claim text")
    source: Literal["new", "cache", "precedent"] = Field(
        default="new",
        description="Source of claim result: new (needs trial), cache (exact match), precedent (similar found)"
    )
    cache_id: Optional[str] = Field(None, description="ID of cached result if source is cache")
    cached_verdict: Optional[str] = Field(None, description="Cached verdict if available")
    precedents: List[Precedent] = Field(default_factory=list, description="Similar historical precedents")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class JuryVote(BaseModel):
    """A single jury member's vote on a claim."""
    
    jury_name: str = Field(..., description="Name/identifier of the jury")
    claim_id: str = Field(..., description="The claim being evaluated")
    decision: Literal["no_objection", "suspicious_fact", "reasonable_doubt", "abstain"] = Field(
        ...,
        description="Jury's decision: no_objection (accept), suspicious_fact (some doubt), reasonable_doubt (reject), abstain (unable to vote/error)"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level (0.0-1.0)")
    reason: str = Field(..., description="Reasoning behind the decision")
    reference_summary: Optional[str] = Field(
        None,
        description="Summary of references/evidence used"
    )
    search_cycles: int = Field(default=1, description="Number of search cycles performed (STEEL framework)")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp of vote")
    
    def is_objection(self) -> bool:
        """Check if this vote is an objection (abstain is not counted as objection)."""
        return self.decision in ["suspicious_fact", "reasonable_doubt"]


class ClaimResult(BaseModel):
    """Result of evaluating a single claim."""
    
    claim: Claim = Field(..., description="The claim that was evaluated")
    jury_votes: List[JuryVote] = Field(default_factory=list, description="Votes from all jury members")
    verdict: str = Field(..., description="Final verdict (e.g., supported, suspicious, refuted)")
    judge_reasoning: str = Field(..., description="Judge's reasoning for the verdict")
    objection_count: int = Field(default=0, description="Number of objections raised")
    objection_ratio: float = Field(default=0.0, description="Ratio of objections to total votes")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp of result")
    
    def calculate_objection_stats(self) -> None:
        """Calculate objection statistics from jury votes."""
        if not self.jury_votes:
            self.objection_count = 0
            self.objection_ratio = 0.0
            return
        
        self.objection_count = sum(1 for vote in self.jury_votes if vote.is_objection())
        self.objection_ratio = self.objection_count / len(self.jury_votes)


class CaseReport(BaseModel):
    """Final report for an entire case."""
    
    case_id: str = Field(..., description="Unique case identifier")
    case_text: str = Field(..., description="Original case text")
    domain: str = Field(default="general", description="Domain of the case")
    status: Literal["completed", "mistrial", "partial"] = Field(
        ...,
        description="Status: completed (success), mistrial (failed quorum), partial (some claims failed)"
    )
    claims: List[ClaimResult] = Field(default_factory=list, description="Results for each claim")
    overall_verdict: Optional[str] = Field(None, description="Overall verdict if applicable")
    error_message: Optional[str] = Field(None, description="Error message if status is not completed")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp of report")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    def get_verdicts_summary(self) -> Dict[str, int]:
        """Get summary of verdicts across all claims."""
        summary: Dict[str, int] = {}
        for claim_result in self.claims:
            verdict = claim_result.verdict
            summary[verdict] = summary.get(verdict, 0) + 1
        return summary


class CourtCodeEntry(BaseModel):
    """Entry in the court_code (precedent database)."""
    
    entry_id: str = Field(default_factory=generate_id, description="Unique entry identifier")
    claim: str = Field(..., description="The claim text")
    verdict: str = Field(..., description="The verdict given")
    reasoning: str = Field(..., description="Reasoning behind the verdict")
    domain: str = Field(default="general", description="Domain of the case")
    case_id: str = Field(..., description="Original case ID")
    
    # Validity period
    timestamp: datetime = Field(default_factory=datetime.now, description="When this entry was created")
    valid_from: Optional[datetime] = Field(None, description="Validity start date")
    valid_until: Optional[datetime] = Field(None, description="Validity end date")
    
    # Statistics
    jury_votes_count: int = Field(default=0, description="Number of jury votes")
    objection_count: int = Field(default=0, description="Number of objections")
    objection_ratio: float = Field(default=0.0, description="Ratio of objections")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    def is_valid(self, check_date: Optional[datetime] = None) -> bool:
        """Check if this entry is currently valid."""
        check_date = check_date or datetime.now()
        if self.valid_from and check_date < self.valid_from:
            return False
        if self.valid_until and check_date > self.valid_until:
            return False
        return True


class ProsecutorReport(BaseModel):
    """Report from the Prosecutor after processing a case."""
    
    case_id: str = Field(..., description="Case identifier")
    original_text: str = Field(..., description="Original case text")
    claims: List[Claim] = Field(default_factory=list, description="Extracted claims")
    rejected: bool = Field(default=False, description="Whether the case was rejected")
    rejection_reason: Optional[str] = Field(None, description="Reason for rejection if applicable")
    cache_hits: int = Field(default=0, description="Number of cache hits")
    precedents_found: int = Field(default=0, description="Number of precedents found")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp of report")


class ModelConfig(BaseModel):
    """Configuration for an LLM model."""
    
    provider: str = Field(..., description="Provider name (e.g., openai, google, anthropic)")
    model_name: str = Field(..., description="Model name/identifier")
    api_key: Optional[str] = Field(None, description="API key if required")
    base_url: Optional[str] = Field(None, description="Base URL for custom endpoints")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate")
    timeout: int = Field(default=60, description="Request timeout in seconds")
    extra_params: Dict[str, Any] = Field(default_factory=dict, description="Additional provider-specific parameters")

