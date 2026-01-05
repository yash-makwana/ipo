"""
Re-analysis Agent - LOCAL VERSION
================
Responsible for refining UNCLEAR or low-confidence cases
Uses local Gemini API (not VertexAI)
"""

import time
import json
from typing import Dict, Any, List
import sys
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from state_models import ComplianceState, ReanalysisOutput, update_agent_path
from semantic_legal_search import get_semantic_search

load_dotenv(".env-local")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY missing from .env-local")


class ReanalysisAgent:
    """
    Re-analysis Agent - Iterative Refinement (LOCAL)
    
    Responsibilities:
    1. Receive cases flagged for reanalysis
    2. Gather additional context (broader search)
    3. Re-analyze with enhanced prompting
    4. Track iteration attempts
    5. Return improved results or escalate if still unclear
    """
    
    def __init__(self, regulation_type: str = "ICDR"):
        """
        Initialize Re-analysis Agent with local Gemini
        
        Args:
            regulation_type: ICDR or Companies Act
        """
        self.regulation_type = regulation_type
        
        # Initialize local Gemini client
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        
        models_to_try = [
            "gemini-2.5-flash-lite",   # 4K RPM - BEST
            "gemini-2.0-flash-lite",   # 4K RPM
            "gemini-2.0-flash",        # 2K RPM
            "gemini-2.5-flash",        # 1K RPM
        ]
        
        self.model_name = None
        for model_name in models_to_try:
            try:
                self.client.models.get(model=model_name)
                self.model_name = model_name
                print(f"✅ ReanalysisAgent initialized with {model_name}")
                break
            except:
                continue
        
        if self.model_name is None:
            self.model_name = "gemini-2.5-flash-lite"
            print(f"⚠️  Using default model: {self.model_name}")
        
        # Initialize semantic search for broader searches
        try:
            self.semantic_search = get_semantic_search(regulation_type)
        except Exception as e:
            print(f"⚠️  Semantic search not available: {e}")
            self.semantic_search = None
    
    def get_additional_legal_context(self, state: ComplianceState) -> List[Dict[str, Any]]:
        """
        Retrieve additional legal requirements with broader query
        
        Args:
            state: Current state
        
        Returns:
            Additional legal requirements
        """
        if not self.semantic_search:
            return []
        
        print(f"   🔍 Searching for additional legal context...")
        
        try:
            # Create broader search query
            broader_query = f"{state.requirement} {state.drhp_chapter}"
            
            # Search with more results
            results = self.semantic_search.vector_search(
                query=broader_query,
                top_k=5
            )
            
            # Filter out already retrieved requirements
            existing_ids = {req.get('obligation_id') or req.get('chunk_id', '') 
                          for req in state.legal_requirements}
            new_results = [r for r in results 
                          if (r.get('obligation_id') or r.get('chunk_id', '')) not in existing_ids]
            
            if new_results:
                print(f"   ✅ Found {len(new_results)} additional legal requirements")
            
            return new_results[:3]
            
        except Exception as e:
            print(f"   ⚠️  Error getting additional context: {e}")
            return []
    
    def build_reanalysis_prompt(self, state: ComplianceState, additional_context: List[Dict]) -> str:
        """
        Build enhanced prompt for reanalysis
        
        Args:
            state: Current state
            additional_context: Additional legal requirements
        
        Returns:
            Enhanced prompt string
        """
        # Original analysis summary
        original_analysis = f"""
PREVIOUS ANALYSIS (Attempt {state.reanalysis_count}):
Status: {state.status}
Confidence: {state.confidence:.2f}
Explanation: {state.explanation}
Issues: {', '.join(state.validation_issues) if state.validation_issues else 'None specified'}
"""
        
        # Format user content
        user_content = ""
        if state.user_relevant_chunks:
            user_content = "\n\n".join([
                f"[Page {chunk.get('page_number', '?')}]: {chunk['text'][:600]}"
                for chunk in state.user_relevant_chunks
            ])
        else:
            user_content = "(No relevant content found)"
        
        # Format legal requirements (original + additional)
        all_legal_reqs = state.legal_requirements + additional_context
        
        legal_context = ""
        if all_legal_reqs:
            legal_context = "\n\nLEGAL REQUIREMENTS:\n"
            for i, legal in enumerate(all_legal_reqs, 1):
                citation = legal.get('citation', '')
                if not citation:
                    # Fallback
                    if legal.get('regulation_number'):
                        citation = f"Regulation {legal['regulation_number']}"
                    elif legal.get('section_number'):
                        citation = f"Section {legal['section_number']}"
                    else:
                        citation = "General Requirement"
                
                req_text = legal.get('requirement_text') or legal.get('text', '')
                legal_context += f"\n[{citation}]: {req_text[:400]}\n"
        
        prompt = f"""You are a compliance expert re-analyzing a case that was previously marked as UNCLEAR or had low confidence.

{original_analysis}

REQUIREMENT:
{state.requirement}

USER DRHP CONTENT:
{user_content}
{legal_context}

TASK: Re-analyze with more careful attention. The previous analysis was unclear - now determine a definitive status.

GUIDELINES FOR THIS REANALYSIS:
1. If there is ANY mention of the requirement (even brief), mark as INSUFFICIENT rather than MISSING
2. If content is truly absent, mark as MISSING
3. Only mark as UNCLEAR if the content is genuinely ambiguous (not just incomplete)
4. Be more decisive - aim for PRESENT, INSUFFICIENT, or MISSING rather than UNCLEAR
5. Provide VERY specific missing details if INSUFFICIENT

Respond with JSON ONLY:
{{
    "status": "PRESENT|INSUFFICIENT|MISSING|UNCLEAR",
    "explanation": "Clear explanation of your determination",
    "evidence": "Specific quotes from user content",
    "missing_details": "Ultra-specific list of missing items",
    "confidence": 0.0-1.0,
    "reanalysis_notes": "What changed from previous analysis"
}}

REMEMBER:
- UNCLEAR should only be used if content is genuinely ambiguous
- If user mentions the topic at all → INSUFFICIENT (not UNCLEAR)
- If user doesn't mention topic at all → MISSING (not UNCLEAR)
- Be decisive and specific!
"""
        
        return prompt
    
    def execute(self, state: ComplianceState) -> ComplianceState:
        """
        Execute re-analysis agent
        
        Args:
            state: Current state needing reanalysis
        
        Returns:
            Updated state with refined analysis
        """
        print(f"\n{'='*60}")
        print(f"🔄 RE-ANALYSIS AGENT (Attempt {state.reanalysis_count + 1})")
        print(f"{'='*60}")
        print(f"Reason: {', '.join(state.validation_issues[:2]) if state.validation_issues else 'Low confidence'}")
        
        start_time = time.time()
        
        # Update agent path and counter
        state = update_agent_path(state, f"REANALYSIS_{state.reanalysis_count + 1}")
        
        # Store previous analysis in history
        state.reanalysis_history.append({
            'attempt': state.reanalysis_count,
            'status': state.status,
            'confidence': state.confidence,
            'explanation': state.explanation
        })
        
        state.reanalysis_count += 1
        
        # Get additional legal context
        additional_context = self.get_additional_legal_context(state)
        
        # Build enhanced prompt
        prompt = self.build_reanalysis_prompt(state, additional_context)
        
        # Re-analyze with LLM
        max_retries = 2
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
                
                # Clean JSON
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0]
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0]
                
                result = json.loads(text.strip())
                
                # Update state with refined analysis
                old_status = state.status
                old_confidence = state.confidence
                
                state.status = result['status']
                state.explanation = result['explanation']
                state.evidence = result.get('evidence', '')
                state.missing_details = result.get('missing_details', '')
                state.confidence = float(result.get('confidence', 0.7))
                
                # Add any new legal requirements found
                if additional_context:
                    state.legal_requirements.extend(additional_context)
                
                elapsed_ms = (time.time() - start_time) * 1000
                
                print(f"\n✅ Re-analysis Complete:")
                print(f"   Previous: {old_status} (confidence: {old_confidence:.2f})")
                print(f"   Updated:  {state.status} (confidence: {state.confidence:.2f})")
                print(f"   Added Context: {len(additional_context)} legal requirements")
                print(f"   Time: {elapsed_ms:.0f}ms")
                
                # Check if improvement
                if state.status != "UNCLEAR" and state.status != old_status:
                    print(f"   🎯 Status improved!")
                elif state.confidence > old_confidence:
                    print(f"   📈 Confidence improved!")
                
                return state
                
            except Exception as e:
                print(f"   ⚠️  Re-analysis attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                else:
                    print(f"   ⚠️  Re-analysis failed, keeping original analysis")
                    return state
        
        return state


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """Test Re-analysis Agent"""
    
    print("=" * 80)
    print("🧪 TESTING RE-ANALYSIS AGENT")
    print("=" * 80)
    
    from state_models import create_initial_state
    
    # Create test state with UNCLEAR status
    state = create_initial_state(
        requirement="Board composition must be disclosed with independent directors",
        drhp_chapter="CHAPTER_V_ABOUT_COMPANY",
        user_document_chunks=[],
        regulation_type="ICDR"
    )
    
    # Simulate previous analysis that was unclear
    state.status = "UNCLEAR"
    state.explanation = "Cannot determine if board composition is adequate"
    state.evidence = "Board has directors"
    state.missing_details = "Need more information"
    state.confidence = 0.45
    
    state.user_relevant_chunks = [
        {
            'text': 'Our board consists of experienced directors. The board includes independent directors.',
            'page_number': 25,
            'relevance_score': 0.75
        }
    ]
    
    state.legal_requirements = [
        {
            'requirement_text': 'Board must have at least 1/3 independent directors. Disclosure must include names and DIN.',
            'citation': 'Companies Act, Section 149',
            'obligation_id': 'COMPANIES_ACT_SEC149',
            'similarity_score': 0.82
        }
    ]
    
    state.validation_issues = ["Status is UNCLEAR", "Confidence too low (0.45)"]
    state.needs_reanalysis = True
    
    # Execute re-analysis
    agent = ReanalysisAgent(regulation_type="Companies Act")
    result_state = agent.execute(state)
    
    # Display results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    print(f"Reanalysis Count: {result_state.reanalysis_count}")
    print(f"New Status: {result_state.status}")
    print(f"New Confidence: {result_state.confidence:.2f}")
    print(f"\nNew Explanation:")
    print(f"  {result_state.explanation}")
    
    print("\n✅ Re-analysis Agent Test Complete!")