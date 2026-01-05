"""
Analysis Agent - WITH PROPER PAGE EXTRACTION
============================================
Analyzes whether user's DRHP satisfies legal obligations
Extracts pages from retrieved chunks
"""

import time
import json
import traceback
from typing import Dict, Any
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from state_models import ComplianceState, update_agent_path
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv('.env-local')
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def safe_parse_json(text: str) -> Dict[str, Any]:
    """Safely parse JSON from LLM response"""
    text = text.strip()
    
    # Remove markdown code blocks
    if '```json' in text:
        text = text.split('```json')[1].split('```')[0]
    elif '```' in text:
        text = text.split('```')[1].split('```')[0]
    
    text = text.strip()
    
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"⚠️  JSON parse error: {e}")
        print(f"   Text: {text[:200]}...")
        return {
            'status': 'UNCLEAR',
            'explanation': 'Failed to parse LLM response',
            'evidence': '',
            'missing_details': '',
            'confidence': 0.3
        }


class AnalysisAgent:
    """
    Analysis Agent - Determines compliance status
    NOW WITH PROPER PAGE EXTRACTION
    """
    
    def __init__(self, regulation_type: str = "ICDR"):
        """Initialize Analysis Agent"""
        self.regulation_type = regulation_type
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        
        # Try models in order
        models_to_try = [
            "gemini-2.5-flash-lite",
            "gemini-2.0-flash-lite",
            "gemini-2.0-flash",
            "gemini-2.5-flash",
            "gemini-2.0-flash-exp",
        ]
        
        self.model_name = None
        for model in models_to_try:
            try:
                test_response = self.client.models.generate_content(
                    model=model,
                    contents="Test",
                    config=types.GenerateContentConfig(
                        temperature=0.1,
                        max_output_tokens=10,
                    )
                )
                self.model_name = model
                break
            except:
                continue
        
        if not self.model_name:
            self.model_name = "gemini-2.0-flash-exp"
        
        print(f"✅ AnalysisAgent initialized with {self.model_name}")
    
    def build_analysis_prompt(self, state: ComplianceState) -> str:
        """Build comprehensive analysis prompt"""
        
        # Format user content
        user_content = ""
        if state.user_relevant_chunks:
            user_content = "\n\n".join([
                f"[Page {c.get('page_number', 'unknown')}]\n{c['text'][:500]}"
                for c in state.user_relevant_chunks[:3]
            ])
        else:
            user_content = "No relevant content found in user's DRHP."
        
        # Format legal requirements
        legal_context = ""
        if state.legal_requirements:
            legal_context = "\n\n".join([
                f"Legal Requirement {i+1}:\n{req.get('text', req.get('search_text', ''))[:400]}"
                for i, req in enumerate(state.legal_requirements[:2])
            ])
        
        prompt = f"""You are a SEBI/Companies Act compliance expert analyzing IPO documents.

LEGAL OBLIGATION TO VERIFY:
{state.requirement}

CONTEXT FROM LEGAL DATABASE:
{legal_context if legal_context else "No additional legal context available."}

USER'S DRHP CONTENT:
{user_content}

TASK: Determine if the user's DRHP satisfies this legal obligation.

STATUS DEFINITIONS:
- PRESENT: Obligation is FULLY satisfied with COMPLETE required information
- INSUFFICIENT: Obligation is PARTIALLY addressed but MISSING specific required details
- MISSING: NO relevant information found in DRHP addressing this obligation
- UNCLEAR: Information exists but is AMBIGUOUS or cannot determine compliance

RESPONSE FORMAT (JSON only, no markdown, no backticks):
{{
  "status": "PRESENT|INSUFFICIENT|MISSING|UNCLEAR",
  "explanation": "Clear explanation of your determination (max 200 words)",
  "evidence": "DIRECT QUOTE from DRHP if content was found (max 150 words, empty string if nothing found)",
  "missing_details": "SPECIFIC, ACTIONABLE list of missing items (if INSUFFICIENT/MISSING)",
  "confidence": 0.0-1.0
}}

CRITICAL INSTRUCTIONS:
1. For "evidence" field:
   - If status is PRESENT or INSUFFICIENT: Include EXACT quote from the DRHP
   - If status is MISSING: Use empty string ""
   - Evidence should be VERBATIM text from user's document

2. For "missing_details" field:
   - Be ULTRA-SPECIFIC and ACTIONABLE
   - ❌ BAD: "More details needed"
   - ✅ GOOD: "Director names and DIN numbers, Board meeting dates for last 3 years, Details of audit committee composition"
   - List items clearly separated by commas

3. For "confidence" scoring:
   - 0.9-1.0: Very confident (clear evidence present or clearly absent)
   - 0.7-0.89: Confident (good evidence)
   - 0.5-0.69: Moderate (partial evidence or ambiguous)
   - Below 0.5: Low confidence (unclear or insufficient context)

Now analyze and return ONLY the JSON object:"""
        
        return prompt
    
    def execute(self, state: ComplianceState) -> ComplianceState:
        """
        Execute analysis agent with PAGE EXTRACTION
        """
        print(f"\n{'='*60}")
        print(f"🔬 ANALYSIS AGENT")
        print(f"{'='*60}")
        print(f"Analyzing: {state.requirement[:60]}...")
        
        start_time = time.time()
        
        # Update agent path
        state = update_agent_path(state, "ANALYSIS")
        
        # ✅ EXTRACT PAGES FIRST (before any analysis)
        pages = []
        if state.user_relevant_chunks:
            for chunk in state.user_relevant_chunks:
                # Try different possible field names
                page = chunk.get('page_number') or chunk.get('page') or chunk.get('pageNumber')
                if page and page != 0:
                    pages.append(page)
            
            # Remove duplicates and sort
            if pages:
                pages = sorted(list(set(pages)))
        
        # ✅ DEBUG: Show page extraction
        print(f"\n   ═══ DEBUG: Page Extraction ═══")
        print(f"   User chunks: {len(state.user_relevant_chunks) if state.user_relevant_chunks else 0}")
        print(f"   Pages found: {pages}")
        if state.user_relevant_chunks and not pages:
            print(f"   ⚠️  WARNING: Chunks exist but no pages extracted!")
            print(f"   Sample chunk keys: {list(state.user_relevant_chunks[0].keys()) if state.user_relevant_chunks else 'None'}")
        print(f"   ═══════════════════════════════\n")
        
        # Check if we have content to analyze
        if not state.user_relevant_chunks and not state.legal_requirements:
            print(f"   ⚠️  No content available for analysis")
            state.status = "MISSING"
            state.explanation = f"No relevant content found addressing: {state.requirement}"
            state.evidence = ""
            state.missing_details = state.requirement
            state.confidence = 0.9
            state.pages = pages
            return state
        
        # Build prompt
        prompt = self.build_analysis_prompt(state)
        
        # Call LLM with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.1,
                        max_output_tokens=2000,
                    )
                )
                
                text = response.text.strip()
                
                # Use safe parser
                result = safe_parse_json(text)
                
                # Update state with parsed results
                state.status = result.get('status', 'UNCLEAR')
                state.explanation = result.get('explanation', 'No explanation provided')
                state.evidence = result.get('evidence', '')
                state.missing_details = result.get('missing_details', '')
                state.confidence = float(result.get('confidence', 0.5))
                
                # ✅ SET PAGES (from extraction above, not from LLM)
                state.pages = pages
                
                elapsed_ms = (time.time() - start_time) * 1000
                
                # ✅ DEBUG: Verify pages are set
                print(f"\n   ═══ DEBUG: Analysis Result ═══")
                print(f"   Status: {state.status}")
                print(f"   Confidence: {state.confidence:.2f}")
                print(f"   Pages in state: {state.pages}")
                print(f"   Pages type: {type(state.pages)}")
                print(f"   ═══════════════════════════════\n")
                
                print(f"\n✅ Analysis Complete:")
                print(f"   Status: {state.status}")
                print(f"   Confidence: {state.confidence:.2f}")
                print(f"   Pages: {state.pages}")
                print(f"   Time: {elapsed_ms:.0f}ms")
                
                return state
                
            except Exception as e:
                error_str = str(e)
                
                # Check for rate limit
                if "429" in error_str or "Resource exhausted" in error_str or "quota" in error_str.lower():
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) * 2
                        print(f"   ⏳ Rate limit (attempt {attempt+1}/{max_retries}), waiting {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                
                # Other errors
                print(f"   ❌ Analysis failed: {e}")
                traceback.print_exc()
                state.status = "UNCLEAR"
                state.explanation = f"Analysis error: {str(e)}"
                state.confidence = 0.3
                state.pages = pages  # ✅ Set pages even on error
                
                # ✅ DEBUG: Show pages on error
                print(f"\n   ═══ DEBUG: Error - Pages Set ═══")
                print(f"   Pages on error: {state.pages}")
                print(f"   ═══════════════════════════════\n")
                
                return state
        
        # Max retries exceeded
        print(f"   ❌ Analysis failed after {max_retries} attempts")
        state.status = "UNCLEAR"
        state.explanation = "Rate limit exceeded"
        state.confidence = 0.3
        state.pages = pages  # ✅ Set pages even after max retries
        
        # ✅ DEBUG: Show pages on max retries
        print(f"\n   ═══ DEBUG: Max Retries - Pages Set ═══")
        print(f"   Pages after max retries: {state.pages}")
        print(f"   ═══════════════════════════════════════\n")
        
        return state