from google import genai
from google.genai import types
import os
import json
from typing import Dict, Any

class QueryDrafter:
    """
    Phase 3: The Verdict
    LLM drafts NSE-style queries based on findings and regulations
    """
    
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
        
        # Find available model
        models_to_try = [
                    "gemini-3-pro",
                    "gemini-2.5-flash-lite",
                    "gemini-2.0-flash-lite",
                    "gemini-2.0-flash",
                    "gemini-2.5-flash",
                    "gemini-2.0-flash-exp"
                ]
        
        self.model_name = None
        for model in models_to_try:
            try:
                self.client.models.generate_content(
                    model=model,
                    contents="Test",
                    config=types.GenerateContentConfig(max_output_tokens=10)
                )
                self.model_name = model
                break
            except:
                continue
        
        print(f"✅ Query Drafter initialized with {self.model_name}")
    
    def draft_query(
        self, 
        finding: Dict, 
        regulation: Dict
    ) -> Dict[str, Any]:
        """
        Draft NSE-style query from finding and regulation
        
        Args:
            finding: From forensic scanner
            regulation: From regulation mapper
        
        Returns:
            Formatted query
        """
        
        # Build prompt
        prompt = self._build_drafting_prompt(finding, regulation)
        
        # Call LLM
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    max_output_tokens=800
                )
            )
            
            query_text = response.text.strip()
            
            return {
                'page': finding['page'],
                'query': query_text,
                'severity': finding['severity'],
                'category': finding['category'],
                'issue_id': finding['issue_id'],
                'regulation_ref': regulation['citation']
            }
            
        except Exception as e:
            print(f"   ❌ LLM drafting failed: {e}")
            
            # Fallback to template
            return self._fallback_template(finding, regulation)
    
    def _build_drafting_prompt(self, finding: Dict, regulation: Dict) -> str:
        """Build precise prompt for LLM"""
        
        return f"""You are drafting an NSE observation letter for an IPO DRHP review.

ROLE: Senior Compliance Officer at NSE

FINDING:
- Page: {finding['page']}
- Issue: {finding['issue_id'].replace('_', ' ').title()}
- Text Found: "{finding['snippet'][:200]}..."
- Matched: "{finding['matched_text']}"

REQUIREMENT:
{finding['template']}

LEGAL BASIS:
{regulation['regulation_text']}
Citation: {regulation['citation']}

TASK:
Draft a professional NSE-style query in this EXACT format:

"On page no. {finding['page']}, it is mentioned [observation]. Kindly [specific request with details]. Provide revised draft along with confirmation that the same shall be updated in prospectus."

CRITICAL RULES:
1. Start with "On page no. X"
2. Be specific about what's missing
3. Use "Kindly" before requests
4. End with "Provide revised draft along with confirmation..."
5. Be professional and respectful
6. Reference the specific issue found

Generate the query now:"""
    
    def _fallback_template(self, finding: Dict, regulation: Dict) -> Dict:
        """Fallback to template if LLM fails"""
        
        template = finding['template']
        
        # Replace placeholders
        query = template.replace('{anchor_pages}', str(finding['page']))
        query = query.replace('{snippet}', finding['matched_text'])
        
        return {
            'page': finding['page'],
            'query': query,
            'severity': finding['severity'],
            'category': finding['category'],
            'issue_id': finding['issue_id'],
            'regulation_ref': regulation['citation']
        }


def get_query_drafter():
    """Factory function"""
    return QueryDrafter()