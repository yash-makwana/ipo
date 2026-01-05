"""
NSE-Style Query Generator Agent
================================
Transforms compliance check results into professional stock exchange queries
matching NSE/BSE format and tone.

Features:
1. Extracts actual company data from DRHP
2. Cites specific pages, figures, names from document
3. Professional NSE/regulatory tone
4. Proper regulation citations
5. Evidence-based observations
"""

import re
import json
from typing import Dict, List, Any, Optional
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

load_dotenv('.env-local')
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


class QueryGeneratorAgent:
    """
    Generates NSE/BSE-style queries from compliance results
    """
    
    def __init__(self):
        """Initialize Query Generator"""
        
        # Check if API key is available
        if GEMINI_API_KEY and GEMINI_API_KEY != "None":
            self.client = genai.Client(api_key=GEMINI_API_KEY)
            
            # Try models in order
            models_to_try = [
                "gemini-2.0-flash-exp",
                "gemini-2.0-flash-lite",
                "gemini-2.5-flash-lite",
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
            
            print(f"✅ QueryGeneratorAgent initialized with {self.model_name}")
        else:
            self.client = None
            self.model_name = "gemini-2.0-flash-exp (simulated)"
            print(f"⚠️  QueryGeneratorAgent initialized in SIMULATION MODE (no API key)")
    
    def extract_company_context(self, drhp_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract company-specific information from DRHP chunks
        
        Args:
            drhp_chunks: Document chunks from DRHP
        
        Returns:
            Dictionary with company name, industry, key figures etc.
        """
        
        context = {
            'company_name': None,
            'industry': None,
            'key_figures': [],
            'key_people': [],
            'locations': []
        }
        
        # Look in first few pages for company info
        first_pages_text = ""
        for chunk in drhp_chunks[:10]:  # First 10 chunks usually have company info
            first_pages_text += chunk.get('text', '') + "\n"
        
        # Extract company name (usually "XXX Limited" or "XXX Private Limited")
        company_pattern = r'([A-Z][A-Za-z\s&]+(?:Limited|Private Limited|Pvt\.?\s*Ltd\.?|Ltd\.?))'
        companies = re.findall(company_pattern, first_pages_text)
        if companies:
            # Get most common one
            from collections import Counter
            context['company_name'] = Counter(companies).most_common(1)[0][0]
        
        # Extract currency amounts (₹XX.XX lakhs/crores)
        amount_pattern = r'₹\s*[\d,]+\.?\d*\s*(?:lakhs?|crores?|million|billion)'
        context['key_figures'] = list(set(re.findall(amount_pattern, first_pages_text, re.IGNORECASE)))[:10]
        
        # Extract person names (Mr./Ms./Dr. followed by capitalized names)
        people_pattern = r'(?:Mr\.|Ms\.|Dr\.|Mrs\.)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+'
        context['key_people'] = list(set(re.findall(people_pattern, first_pages_text)))[:10]
        
        return context
    
    def generate_query(
        self,
        compliance_result: Dict[str, Any],
        drhp_chunks: List[Dict[str, Any]],
        company_context: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Generate NSE-style query from compliance result
        
        Args:
            compliance_result: Result from compliance check
            drhp_chunks: Document chunks for context
            company_context: Extracted company information
        
        Returns:
            Formatted query dictionary
        """
        
        # Build context from evidence
        evidence_text = compliance_result.get('evidence', '')
        missing_details = compliance_result.get('missing_details', '')
        pages = compliance_result.get('pages', [])
        status = compliance_result.get('status', 'UNCLEAR')
        obligation = compliance_result.get('obligation', '')
        citation = compliance_result.get('citation', '')
        
        # Get actual text from pages for context
        page_context = ""
        if pages:
            for chunk in drhp_chunks:
                chunk_page = chunk.get('page_number') or chunk.get('page', 0)
                if chunk_page in pages:
                    page_context += chunk.get('text', '')[:500] + "\n"
        
        # Build prompt for LLM
        prompt = f"""You are a regulatory analyst from NSE/BSE drafting compliance queries for an IPO DRHP.

COMPANY INFORMATION:
- Company Name: {company_context.get('company_name', 'the Company')}
- Industry: {company_context.get('industry', 'Not specified')}

COMPLIANCE CHECK RESULT:
- Obligation: {obligation}
- Status: {status}
- Regulation Reference: {citation}
- Pages Referenced: {pages if pages else 'Not found'}
- Evidence Found: {evidence_text if evidence_text else 'No evidence found'}
- Missing Details: {missing_details}

CONTEXT FROM DRHP (Page {pages[0] if pages else 'unknown'}):
{page_context[:800]}

TASK: Write a professional NSE-style compliance query following this EXACT format:

[Clear Title]
On page [X], [specific observation from DRHP with actual text/numbers]. [Detailed explanation of issue]. 

Recommendation: Kindly [specific action required].

Regulation Ref: [Specific regulation citation]

[Severity]: Major/Minor/Critical

Page [X]

CRITICAL RULES:
1. MUST quote ACTUAL TEXT from the DRHP context provided above
2. MUST use the company name: "{company_context.get('company_name', 'the Company')}"
3. MUST cite specific numbers/figures if present
4. MUST be respectful and professional: use "Kindly provide...", "Kindly clarify..."
5. If STATUS is MISSING → "Kindly disclose/provide..."
6. If STATUS is INSUFFICIENT → "Kindly elaborate/clarify..."
7. If STATUS is UNCLEAR → "Kindly clarify the ambiguity..."
8. NEVER use generic phrases like "the document states" - quote actual text
9. Page numbers MUST match the pages from compliance result: {pages}

SEVERITY MAPPING:
- MISSING + mandatory obligation → Critical
- MISSING + non-mandatory → Major
- INSUFFICIENT → Major or Minor based on importance
- UNCLEAR → Minor

Now generate the query:"""

        try:
            if not self.client:
                # Simulation mode - create template query
                raise Exception("No API client - using simulation mode")
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=1500,
                )
            )
            
            query_text = response.text.strip()
            
            # Parse the generated query to extract components
            title_match = re.search(r'^(.+?)(?=\nOn page)', query_text, re.MULTILINE)
            page_match = re.search(r'Page\s+(\d+)', query_text)
            severity_match = re.search(r'(Critical|Major|Minor):', query_text)
            regulation_match = re.search(r'Regulation Ref:\s*(.+?)(?=\n|$)', query_text)
            
            return {
                'title': title_match.group(1).strip() if title_match else "Compliance Query",
                'full_query': query_text,
                'page': page_match.group(1) if page_match else (str(pages[0]) if pages else "N/A"),
                'severity': severity_match.group(1) if severity_match else "Minor",
                'regulation': regulation_match.group(1).strip() if regulation_match else citation,
                'status': status,
                'obligation': obligation
            }
            
        except Exception as e:
            print(f"❌ Query generation failed: {e}")
            
            # Fallback: Create basic query
            severity = "Critical" if status == "MISSING" else "Major" if status == "INSUFFICIENT" else "Minor"
            page_str = f"Page {pages[0]}" if pages else "Page N/A"
            
            company_name = company_context.get('company_name', 'the Company')
            
            fallback_query = f"""Compliance Query - {obligation[:60]}
On page {pages[0] if pages else 'N/A'}, it has been observed that {company_name} has not adequately disclosed information regarding: {obligation}.

{evidence_text if evidence_text else 'No relevant information found in the DRHP.'}

Recommendation: Kindly provide complete disclosure as per regulatory requirements. {missing_details}

Regulation Ref: {citation}

{severity}: {page_str}"""

            return {
                'title': f"Compliance Query - {obligation[:60]}",
                'full_query': fallback_query,
                'page': str(pages[0]) if pages else "N/A",
                'severity': severity,
                'regulation': citation,
                'status': status,
                'obligation': obligation
            }
    
    def generate_batch_queries(
        self,
        compliance_results: List[Dict[str, Any]],
        drhp_chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate queries for multiple compliance results
        
        Args:
            compliance_results: List of compliance check results
            drhp_chunks: Document chunks from DRHP
        
        Returns:
            List of formatted queries
        """
        
        print(f"\n{'='*80}")
        print(f"📝 GENERATING NSE-STYLE QUERIES")
        print(f"{'='*80}")
        print(f"   Total Results: {len(compliance_results)}")
        
        # Extract company context once
        company_context = self.extract_company_context(drhp_chunks)
        print(f"   Company: {company_context.get('company_name', 'Not identified')}")
        
        queries = []
        
        for i, result in enumerate(compliance_results, 1):
            print(f"\n   [{i}/{len(compliance_results)}] Generating query...")
            
            query = self.generate_query(
                compliance_result=result,
                drhp_chunks=drhp_chunks,
                company_context=company_context
            )
            
            queries.append(query)
            
            print(f"      ✅ Generated: {query['title'][:60]}...")
            print(f"      Page: {query['page']}, Severity: {query['severity']}")
        
        print(f"\n{'='*80}")
        print(f"✅ Generated {len(queries)} queries")
        print(f"{'='*80}\n")
        
        return queries
    
    def format_queries_by_page(
        self,
        queries: List[Dict[str, Any]]
    ) -> Dict[int, List[Dict[str, Any]]]:
        """
        Organize queries by page number (for page-by-page output)
        
        Args:
            queries: List of query dictionaries
        
        Returns:
            Dictionary mapping page numbers to queries
        """
        
        by_page = {}
        
        for query in queries:
            page = query.get('page', 'N/A')
            
            # Try to convert to int
            try:
                page_num = int(page)
            except:
                page_num = 9999  # Put unparseable pages at end
            
            if page_num not in by_page:
                by_page[page_num] = []
            
            by_page[page_num].append(query)
        
        return dict(sorted(by_page.items()))
    
    def export_to_pdf_format(
        self,
        queries: List[Dict[str, Any]],
        output_file: str = "compliance_queries.txt"
    ) -> str:
        """
        Export queries to text file in NSE format
        
        Args:
            queries: List of query dictionaries
            output_file: Output filename
        
        Returns:
            Path to output file
        """
        
        # Organize by page
        by_page = self.format_queries_by_page(queries)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("DRHP COMPLIANCE QUERIES\n")
            f.write("="*80 + "\n\n")
            
            for page_num in sorted(by_page.keys()):
                page_queries = by_page[page_num]
                
                for query in page_queries:
                    f.write(query['full_query'])
                    f.write("\n\n" + "-"*80 + "\n\n")
        
        print(f"✅ Queries exported to: {output_file}")
        return output_file
