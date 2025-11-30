"""
Court class for Model Court.

The Court is the main orchestrator that coordinates the entire trial process:
1. Prosecutor preprocesses the case
2. Juries evaluate each claim
3. Judge renders final verdicts
4. Results are recorded in court_code
"""

import asyncio
from typing import List, Optional, Dict, Any
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .models import CaseReport, ClaimResult, CourtCodeEntry
from .prosecutor import Prosecutor
from .jury import Jury
from .judge import Judge
from utils.helpers import run_with_concurrency_limit


class Court:
    """
    Main Court class that orchestrates the trial process.
    """
    
    def __init__(
        self,
        prosecutor: Prosecutor,
        juries: List[Jury],
        judge: Judge,
        verdict_rules: Optional[Dict[str, Any]] = None,
        quorum: int = 3,
        concurrency_limit: int = 5
    ):
        """
        Initialize the Court.
        
        Args:
            prosecutor: Prosecutor instance for case preprocessing
            juries: List of Jury instances
            judge: Judge instance for rendering verdicts
            verdict_rules: Rules for determining verdicts (passed to judge if not already set)
            quorum: Minimum number of successful jury votes required
            concurrency_limit: Maximum number of concurrent operations
        """
        self.prosecutor = prosecutor
        self.juries = juries
        self.judge = judge
        self.verdict_rules = verdict_rules
        self.quorum = quorum
        self.concurrency_limit = concurrency_limit
        
        # Validate configuration
        if len(juries) < quorum:
            raise ValueError(
                f"Number of juries ({len(juries)}) must be >= quorum ({quorum})"
            )
    
    async def hear(self, case_text: str, domain: str = "general") -> CaseReport:
        """
        Conduct a full trial for a case.
        
        This is the main entry point for the Court system.
        
        Args:
            case_text: The case text to evaluate
            domain: Domain of the case (e.g., "fact_check", "finance", "law")
        
        Returns:
            CaseReport with results for all claims
        """
        # Step 1: Prosecutor processes the case
        prosecutor_report = await self.prosecutor.process(case_text)
        
        # Generate case ID
        from core.models import generate_id
        case_id = generate_id()
        prosecutor_report.case_id = case_id
        
        # Step 2: Process each claim
        claim_results: List[ClaimResult] = []
        mistrial_occurred = False
        partial_failure = False
        error_message = None
        
        for claim in prosecutor_report.claims:
            try:
                # Handle cached results
                if claim.source == "cache":
                    # Create a claim result from cached verdict
                    cached_result = ClaimResult(
                        claim=claim,
                        jury_votes=[],  # No jury votes needed for cache
                        verdict=claim.cached_verdict,
                        judge_reasoning=f"This claim was previously decided. Using cached verdict from precedent {claim.cache_id}.",
                        objection_count=0,
                        objection_ratio=0.0
                    )
                    claim_results.append(cached_result)
                    continue
                
                # Conduct jury trial for new/precedent claims
                claim_result = await self._conduct_jury_trial(claim)
                
                # Check if we met quorum
                if claim_result is None:
                    mistrial_occurred = True
                    error_message = f"Failed to meet quorum for claim: {claim.text[:50]}..."
                    break
                
                claim_results.append(claim_result)
                
                # Step 3: Record verdict in court_code (for non-cached claims)
                await self._record_verdict(claim_result, case_id, domain)
            
            except Exception as e:
                print(f"Error processing claim: {e}")
                partial_failure = True
                # Continue with other claims
        
        # Step 4: Generate report
        status = "completed"
        if mistrial_occurred:
            status = "mistrial"
        elif partial_failure:
            status = "partial"
        
        report = CaseReport(
            case_id=case_id,
            case_text=case_text,
            domain=domain,
            status=status,
            claims=claim_results,
            error_message=error_message
        )
        
        return report
    
    async def _conduct_jury_trial(self, claim) -> Optional[ClaimResult]:
        """
        Conduct jury trial for a single claim.
        
        Args:
            claim: The claim to evaluate
        
        Returns:
            ClaimResult if quorum met, None otherwise
        """
        # Step 1: Collect jury votes concurrently
        async def get_vote(jury: Jury):
            try:
                return await jury.vote(claim)
            except Exception as e:
                print(f"Warning: {jury.name} failed to vote: {e}")
                return None
        
        # Run jury votes with concurrency limit
        vote_tasks = [get_vote(jury) for jury in self.juries]
        votes = await run_with_concurrency_limit(vote_tasks, self.concurrency_limit)
        
        # Filter out failed votes (None) and abstain votes (弃权视作掉队)
        successful_votes = [v for v in votes if v is not None and v.decision != "abstain"]
        
        # Count abstentions for logging
        abstention_count = sum(1 for v in votes if v is not None and v.decision == "abstain")
        
        # Check quorum
        if len(successful_votes) < self.quorum:
            print(
                f"Mistrial: Only {len(successful_votes)} active votes (excl. {abstention_count} abstentions), "
                f"quorum requires {self.quorum}"
            )
            return None
        
        # Step 2: Judge renders verdict
        result = await self.judge.verdict(
            claim=claim,
            jury_votes=successful_votes,
            precedents=claim.precedents if claim.source == "precedent" else None
        )
        
        return result
    
    async def _record_verdict(
        self,
        claim_result: ClaimResult,
        case_id: str,
        domain: str
    ) -> None:
        """
        Record verdict in court_code for future reference.
        
        Args:
            claim_result: The claim result to record
            case_id: Case ID
            domain: Domain of the case
        """
        try:
            # Create court code entry
            entry = CourtCodeEntry(
                claim=claim_result.claim.text,
                verdict=claim_result.verdict,
                reasoning=claim_result.judge_reasoning,
                domain=domain,
                case_id=case_id,
                jury_votes_count=len(claim_result.jury_votes),
                objection_count=claim_result.objection_count,
                objection_ratio=claim_result.objection_ratio
            )
            
            # Add to court code
            await self.prosecutor.court_code.add_entry(entry)
        
        except Exception as e:
            print(f"Warning: Failed to record verdict in court_code: {e}")
    
    def summary(self, report: CaseReport) -> str:
        """
        Generate a human-readable summary of the case report.
        
        Args:
            report: Case report to summarize
        
        Returns:
            Summary text
        """
        lines = []
        lines.append("=" * 70)
        lines.append(f"CASE REPORT - {report.case_id}")
        lines.append("=" * 70)
        lines.append(f"Status: {report.status.upper()}")
        lines.append(f"Domain: {report.domain}")
        lines.append(f"Total Claims: {len(report.claims)}")
        lines.append("")
        
        # Verdict summary
        verdict_summary = report.get_verdicts_summary()
        lines.append("Verdict Summary:")
        for verdict, count in verdict_summary.items():
            lines.append(f"  - {verdict.upper()}: {count}")
        lines.append("")
        
        # Individual claims
        for i, claim_result in enumerate(report.claims, 1):
            lines.append(f"Claim {i}: {claim_result.claim.text[:80]}...")
            lines.append(f"  Verdict: {claim_result.verdict.upper()}")
            lines.append(f"  Jury Votes: {len(claim_result.jury_votes)} "
                        f"({claim_result.objection_count} objections)")
            
            if claim_result.claim.source == "cache":
                lines.append(f"  [Cached from precedent {claim_result.claim.cache_id}]")
            
            lines.append(f"  Reasoning: {claim_result.judge_reasoning[:150]}...")
            lines.append("")
        
        lines.append("=" * 70)
        
        return "\n".join(lines)

