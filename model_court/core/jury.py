"""
Jury class for Model Court.

Each Jury represents an independent evaluator that assesses claims.
Juries can optionally use reference sources and implement the STEEL framework
for iterative evidence gathering.
"""

from typing import Optional, Dict, Any, List
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .models import Claim, JuryVote
from model_court.references.base import BaseReference
from model_court.llm.factory import create_llm_provider
from model_court.llm.base import BaseLLMProvider


class Jury:
    """
    Jury class for evaluating claims.
    
    Implements the STEEL framework:
    1. Search - Initial evidence retrieval
    2. Think - LLM evaluation of evidence sufficiency
    3. Evaluate - Generate verdict if sufficient
    4. Expand - Generate new queries if insufficient
    5. Loop - Repeat until sufficient or max cycles reached
    """
    
    def __init__(
        self,
        name: str,
        model: Dict[str, Any],
        reference: Optional[BaseReference] = None,
        jury_prompt: Optional[str] = None,
        search_cycle_mode: bool = False,
        search_cycle_max: int = 3
    ):
        """
        Initialize a Jury member.
        
        Args:
            name: Name/identifier for this jury
            model: LLM model configuration
            reference: Reference source for evidence (None = blind mode)
            jury_prompt: Custom prompt for the jury
            search_cycle_mode: Enable STEEL iterative search
            search_cycle_max: Maximum search cycles (for STEEL)
        """
        self.name = name
        self.reference = reference
        self.jury_prompt = jury_prompt
        self.search_cycle_mode = search_cycle_mode
        self.search_cycle_max = search_cycle_max
        
        # Initialize LLM
        self._llm: BaseLLMProvider = create_llm_provider(model)
        
        # Default system prompts
        self._system_prompt = """You are an expert jury member evaluating claims for truthfulness.
Your role is to carefully analyze the claim and any available evidence, then provide your verdict.

You must respond with a JSON object in this exact format:
{
    "decision": "no_objection" | "suspicious_fact" | "reasonable_doubt" | "abstain",
    "confidence": 0.0-1.0,
    "reason": "Your detailed reasoning"
}

Decision meanings:
- "no_objection": The claim appears to be true/valid
- "suspicious_fact": There are some concerns, but not conclusive
- "reasonable_doubt": The claim appears to be false/invalid
- "abstain": Unable to make a determination (abstain from voting)"""
        
        self._sufficiency_prompt = """You are evaluating whether the evidence is sufficient to make a determination.

Evidence collected so far:
{evidence}

Question: Is this evidence sufficient to make a confident determination about the claim?

You MUST respond with ONLY valid JSON in this exact format (no extra text, no quotes around the JSON):
{{
    "sufficient": true,
    "new_query": ""
}}

Or:
{{
    "sufficient": false,
    "new_query": "suggested search query here"
}}
"""
    
    async def vote(self, claim: Claim) -> JuryVote:
        """
        Evaluate a claim and cast a vote.
        
        Args:
            claim: The claim to evaluate
        
        Returns:
            JuryVote with decision and reasoning
        """
        if self.search_cycle_mode and self.reference:
            return await self._vote_with_steel(claim)
        else:
            return await self._vote_simple(claim)
    
    async def _vote_simple(self, claim: Claim) -> JuryVote:
        """
        Simple voting without iterative search.
        
        Args:
            claim: The claim to evaluate
        
        Returns:
            JuryVote
        """
        # Gather evidence if reference is available
        evidence_text = ""
        if self.reference:
            try:
                evidence = await self.reference.retrieve(claim.text, top_k=3)
                if evidence:
                    evidence_text = "\n\nAvailable Evidence:\n" + "\n---\n".join(evidence)
            except Exception as e:
                print(f"Warning: Evidence retrieval failed for {self.name}: {e}")
        
        # Prepare prompt
        user_prompt = f"""Claim to evaluate:
{claim.text}
{evidence_text}

{self.jury_prompt or "Please evaluate this claim carefully."}

Remember to respond with JSON containing: decision, confidence, and reason."""
        
        try:
            # Get verdict from LLM
            response = await self._llm.generate_json(
                prompt=user_prompt,
                system_prompt=self._system_prompt
            )
            
            # Parse response
            decision = response.get("decision", "reasonable_doubt")
            confidence = float(response.get("confidence", 0.5))
            reason = response.get("reason", "No reason provided")
            
            # Create vote
            vote = JuryVote(
                jury_name=self.name,
                claim_id=claim.claim_id,
                decision=decision,
                confidence=confidence,
                reason=reason,
                reference_summary=evidence_text[:200] if evidence_text else None,
                search_cycles=1
            )
            
            return vote
        
        except Exception as e:
            # Fallback vote in case of error - jury abstains (缺席/弃权)
            print(f"Error in {self.name} voting: {e}")
            return JuryVote(
                jury_name=self.name,
                claim_id=claim.claim_id,
                decision="abstain",  # 出错时标记为缺席
                confidence=0.0,
                reason=f"Error during evaluation: {str(e)}",
                search_cycles=1
            )
    
    async def _vote_with_steel(self, claim: Claim) -> JuryVote:
        """
        Voting with STEEL iterative search framework.
        
        STEEL: Search, Think, Evaluate, Expand, Loop
        
        Args:
            claim: The claim to evaluate
        
        Returns:
            JuryVote
        """
        collected_evidence: List[str] = []
        search_cycle = 0
        query = claim.text
        
        # STEEL Loop
        while search_cycle < self.search_cycle_max:
            search_cycle += 1
            
            # SEARCH: Retrieve evidence
            try:
                evidence = await self.reference.retrieve(query, top_k=3)
                collected_evidence.extend(evidence)
            except Exception as e:
                print(f"Warning: Search cycle {search_cycle} failed for {self.name}: {e}")
                break
            
            # THINK: Evaluate sufficiency
            evidence_summary = "\n---\n".join(collected_evidence)
            sufficiency_prompt = self._sufficiency_prompt.format(
                evidence=evidence_summary
            )
            
            try:
                sufficiency_response = await self._llm.generate_json(
                    prompt=sufficiency_prompt,
                    system_prompt="You are evaluating evidence sufficiency. Respond with valid JSON only."
                )
                
                # Handle different response formats
                if isinstance(sufficiency_response, dict):
                    is_sufficient = sufficiency_response.get("sufficient", False)
                    if isinstance(is_sufficient, str):
                        is_sufficient = is_sufficient.lower() in ["true", "yes", "sufficient"]
                elif isinstance(sufficiency_response, str):
                    is_sufficient = sufficiency_response.lower() in ["true", "yes", "sufficient"]
                else:
                    is_sufficient = False
                
                # EVALUATE: If sufficient, generate final verdict
                if is_sufficient:
                    break
                
                # EXPAND: Generate new query
                if isinstance(sufficiency_response, dict):
                    new_query = sufficiency_response.get("new_query")
                    if new_query:
                        query = new_query
                    else:
                        break
                else:
                    break
            
            except Exception as e:
                print(f"Warning: Sufficiency evaluation failed: {e}")
                break
        
        # Generate final verdict based on all collected evidence
        evidence_text = "\n\nCollected Evidence (from {} search cycles):\n{}".format(
            search_cycle,
            "\n---\n".join(collected_evidence)
        )
        
        user_prompt = f"""Claim to evaluate:
{claim.text}
{evidence_text}

{self.jury_prompt or "Please evaluate this claim based on the collected evidence."}

Remember to respond with JSON containing: decision, confidence, and reason."""
        
        try:
            response = await self._llm.generate_json(
                prompt=user_prompt,
                system_prompt=self._system_prompt
            )
            
            decision = response.get("decision", "reasonable_doubt")
            confidence = float(response.get("confidence", 0.5))
            reason = response.get("reason", "No reason provided")
            
            vote = JuryVote(
                jury_name=self.name,
                claim_id=claim.claim_id,
                decision=decision,
                confidence=confidence,
                reason=reason,
                reference_summary=f"Evidence from {search_cycle} search cycles",
                search_cycles=search_cycle
            )
            
            return vote
        
        except Exception as e:
            print(f"Error in {self.name} STEEL voting: {e}")
            return JuryVote(
                jury_name=self.name,
                claim_id=claim.claim_id,
                decision="abstain",  # 出错时标记为缺席
                confidence=0.0,
                reason=f"Error during STEEL evaluation: {str(e)}",
                search_cycles=search_cycle
            )

