"""
Prosecutor class for Model Court.

The Prosecutor is responsible for:
1. Preprocessing the case
2. Splitting the case into individual claims (if enabled)
3. Searching the court_code for existing precedents
4. Determining which claims need trial
"""

from typing import Optional, Dict, Any
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .models import Claim, ProsecutorReport
from model_court.code.base import BaseCourtCode
from model_court.llm.factory import create_llm_provider
from model_court.llm.base import BaseLLMProvider


class Prosecutor:
    """
    Prosecutor class for case preprocessing and precedent search.
    """
    
    def __init__(
        self,
        court_code: BaseCourtCode,
        auto_claim_splitting: bool = False,
        model: Optional[Dict[str, Any]] = None,
        prosecutor_prompt: Optional[str] = None
    ):
        """
        Initialize the Prosecutor.
        
        Args:
            court_code: Court code database for precedent search
            auto_claim_splitting: Whether to automatically split cases into claims
            model: LLM model configuration (required if auto_claim_splitting is True)
            prosecutor_prompt: Custom prompt for the prosecutor (used for claim splitting)
        """
        self.court_code = court_code
        self.auto_claim_splitting = auto_claim_splitting
        self.prosecutor_prompt = prosecutor_prompt
        
        # Initialize LLM if claim splitting is enabled
        self._llm: Optional[BaseLLMProvider] = None
        if auto_claim_splitting:
            if not model:
                raise ValueError("model configuration required when auto_claim_splitting is True")
            self._llm = create_llm_provider(model)
        
        # Default system prompt for claim splitting
        self._default_system_prompt = """You are a prosecutor analyzing a case. Your job is to:
1. Break down the case into individual, verifiable claims
2. Each claim should be independent and testable
3. Return ONLY a JSON array of claims, with no other text

Example format:
["Claim 1", "Claim 2", "Claim 3"]

Important: Return ONLY the JSON array, nothing else."""
    
    async def process(self, case_text: str) -> ProsecutorReport:
        """
        Process a case and prepare it for trial.
        
        Args:
            case_text: The case text to process
        
        Returns:
            ProsecutorReport with extracted claims and precedent search results
        """
        # Step 1: Split into claims (or treat entire case as one claim)
        if self.auto_claim_splitting:
            claim_texts = await self._split_into_claims(case_text)
        else:
            claim_texts = [case_text]
        
        # Step 2: Search precedents for each claim
        claims = []
        cache_hits = 0
        precedents_found = 0
        
        for claim_text in claim_texts:
            # Search for exact match
            exact_match = await self.court_code.search_exact(claim_text)
            
            if exact_match and exact_match.is_valid():
                # Found exact match in valid period -> use cache
                claim = Claim(
                    text=claim_text,
                    source="cache",
                    cache_id=exact_match.entry_id,
                    cached_verdict=exact_match.verdict
                )
                cache_hits += 1
            else:
                # Search for similar precedents
                similar_precedents = await self.court_code.search_similar(
                    claim_text,
                    top_k=5,
                    threshold=0.7
                )
                
                # Filter for valid precedents only
                valid_precedents = [p for p in similar_precedents if p.is_valid()]
                
                if valid_precedents:
                    claim = Claim(
                        text=claim_text,
                        source="precedent",
                        precedents=valid_precedents
                    )
                    precedents_found += len(valid_precedents)
                else:
                    claim = Claim(
                        text=claim_text,
                        source="new"
                    )
            
            claims.append(claim)
        
        # Create report
        report = ProsecutorReport(
            case_id="",  # Will be set by Court
            original_text=case_text,
            claims=claims,
            cache_hits=cache_hits,
            precedents_found=precedents_found
        )
        
        return report
    
    async def _split_into_claims(self, case_text: str) -> list[str]:
        """
        Split case text into individual claims using LLM.
        
        Args:
            case_text: The case text to split
        
        Returns:
            List of individual claim texts
        """
        if not self._llm:
            return [case_text]
        
        # Prepare prompt
        user_prompt = self.prosecutor_prompt or self._default_system_prompt
        full_prompt = f"{user_prompt}\n\nCase to analyze:\n{case_text}"
        
        try:
            # Generate response
            response = await self._llm.generate(
                prompt=full_prompt,
                system_prompt="You are a legal prosecutor analyzing cases."
            )
            
            # Parse JSON response
            import json
            import re
            
            # Try to extract JSON array
            try:
                claims = json.loads(response)
            except json.JSONDecodeError:
                # Try to find JSON array in response
                json_match = re.search(r'\[.*?\]', response, re.DOTALL)
                if json_match:
                    claims = json.loads(json_match.group(0))
                else:
                    # Fallback: treat entire case as one claim
                    return [case_text]
            
            # Validate that we got a list of strings
            if isinstance(claims, list) and all(isinstance(c, str) for c in claims):
                return [c.strip() for c in claims if c.strip()]
            else:
                return [case_text]
        
        except Exception as e:
            print(f"Warning: Claim splitting failed: {e}. Using entire case as one claim.")
            return [case_text]

