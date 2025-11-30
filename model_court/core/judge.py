"""
Judge class for Model Court.

The Judge aggregates jury votes and historical precedents to render
a final verdict on each claim.
"""

from typing import List, Dict, Any, Optional
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .models import Claim, JuryVote, ClaimResult, Precedent
from model_court.llm.factory import create_llm_provider
from model_court.llm.base import BaseLLMProvider
from model_court.utils.helpers import calculate_verdict


class Judge:
    """
    Judge class for rendering final verdicts.
    
    The Judge considers:
    1. Votes from all jury members
    2. Historical precedents (if any)
    3. Verdict rules for decision-making
    """
    
    def __init__(
        self,
        model: Dict[str, Any],
        verdict_rules: Optional[Dict[str, Any]] = None,
        judge_prompt: Optional[str] = None
    ):
        """
        Initialize the Judge.
        
        Args:
            model: LLM model configuration for generating reasoning
            verdict_rules: Rules for determining verdict based on votes
                Example: {
                    "supported": {"operator": "eq", "value": 0},
                    "suspicious": {"operator": "lt", "value": 0.5},
                    "refuted": "default"
                }
            judge_prompt: Custom prompt for the judge
        """
        self._llm: BaseLLMProvider = create_llm_provider(model)
        self.judge_prompt = judge_prompt
        
        # Default verdict rules
        self.verdict_rules = verdict_rules or {
            "supported": {"operator": "eq", "value": 0},      # 0 objections
            "suspicious": {"operator": "lt", "value": 0.5},   # < 50% objections
            "refuted": "default"                               # >= 50% objections
        }
        
        # System prompt for judge
        self._system_prompt = """You are a judge synthesizing jury opinions and historical precedents to explain a verdict.

Your task is to:
1. Summarize the jury votes
2. Consider any historical precedents
3. Provide clear reasoning for the verdict

You must respond with a JSON object:
{
    "reasoning": "Detailed explanation of the verdict"
}"""
    
    async def verdict(
        self,
        claim: Claim,
        jury_votes: List[JuryVote],
        precedents: Optional[List[Precedent]] = None
    ) -> ClaimResult:
        """
        Render a verdict for a claim based on jury votes and precedents.
        
        Args:
            claim: The claim being judged
            jury_votes: Votes from all jury members
            precedents: Historical precedents (if any)
        
        Returns:
            ClaimResult with verdict and reasoning
        """
        # Calculate objection statistics
        objection_count = sum(1 for vote in jury_votes if vote.is_objection())
        objection_ratio = objection_count / len(jury_votes) if jury_votes else 0.0
        
        # Determine verdict using rules
        verdict_decision = calculate_verdict(objection_ratio, self.verdict_rules)
        
        # Generate reasoning using LLM
        reasoning = await self._generate_reasoning(
            claim, jury_votes, precedents, verdict_decision, objection_ratio
        )
        
        # Create result
        result = ClaimResult(
            claim=claim,
            jury_votes=jury_votes,
            verdict=verdict_decision,
            judge_reasoning=reasoning,
            objection_count=objection_count,
            objection_ratio=objection_ratio
        )
        
        return result
    
    async def _generate_reasoning(
        self,
        claim: Claim,
        jury_votes: List[JuryVote],
        precedents: Optional[List[Precedent]],
        verdict: str,
        objection_ratio: float
    ) -> str:
        """
        Generate detailed reasoning for the verdict.
        
        Args:
            claim: The claim
            jury_votes: Jury votes
            precedents: Historical precedents
            verdict: The determined verdict
            objection_ratio: Ratio of objections
        
        Returns:
            Reasoning text
        """
        # Prepare jury votes summary
        votes_summary = []
        for vote in jury_votes:
            votes_summary.append(
                f"- {vote.jury_name}: {vote.decision} (confidence: {vote.confidence:.2f})\n"
                f"  Reason: {vote.reason[:150]}..."
            )
        
        votes_text = "\n".join(votes_summary)
        
        # Prepare precedents summary
        precedents_text = ""
        if precedents:
            prec_summary = []
            for prec in precedents[:3]:  # Limit to top 3
                prec_summary.append(
                    f"- Similar claim (similarity: {prec.similarity_score:.2f}): {prec.claim[:100]}...\n"
                    f"  Previous verdict: {prec.verdict}"
                )
            precedents_text = "\n\nHistorical Precedents:\n" + "\n".join(prec_summary)
        
        # Prepare prompt
        user_prompt = f"""Claim under consideration:
{claim.text}

Jury Votes ({len(jury_votes)} total, {objection_ratio:.1%} objections):
{votes_text}
{precedents_text}

Final Verdict: {verdict.upper()}

{self.judge_prompt or "Please provide a clear, comprehensive explanation for this verdict."}

Respond with JSON containing the reasoning."""
        
        try:
            response = await self._llm.generate_json(
                prompt=user_prompt,
                system_prompt=self._system_prompt
            )
            
            reasoning = response.get("reasoning", "")
            
            # Fallback if reasoning is empty
            if not reasoning:
                reasoning = self._generate_fallback_reasoning(
                    len(jury_votes), objection_ratio, verdict
                )
            
            return reasoning
        
        except Exception as e:
            print(f"Warning: Judge reasoning generation failed: {e}")
            return self._generate_fallback_reasoning(
                len(jury_votes), objection_ratio, verdict
            )
    
    def _generate_fallback_reasoning(
        self,
        total_votes: int,
        objection_ratio: float,
        verdict: str
    ) -> str:
        """
        Generate simple fallback reasoning if LLM fails.
        
        Args:
            total_votes: Total number of votes
            objection_ratio: Ratio of objections
            verdict: The verdict
        
        Returns:
            Simple reasoning text
        """
        objection_count = int(total_votes * objection_ratio)
        
        if verdict == "supported":
            return (
                f"Based on unanimous agreement from {total_votes} jury members "
                f"with no objections raised, this claim is SUPPORTED."
            )
        elif verdict == "suspicious":
            return (
                f"Based on {objection_count} objection(s) out of {total_votes} jury members "
                f"({objection_ratio:.1%}), this claim is considered SUSPICIOUS and requires further investigation."
            )
        else:  # refuted
            return (
                f"Based on {objection_count} objection(s) out of {total_votes} jury members "
                f"({objection_ratio:.1%}), this claim is REFUTED."
            )

