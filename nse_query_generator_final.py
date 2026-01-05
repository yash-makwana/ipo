"""
NSE-Style Query Generator - COMPLETE VERSION
============================================
Final version addressing all 6 issues:
1. ✅ Customized output with company data
2. ✅ Evidence quality (verbatim quotes)
3. ✅ Specific regulation citations
4. ✅ Page-by-page sequential analysis
5. ✅ NSE tone consistency
6. ✅ Cross-page inconsistency detection
"""

import re
import json
from typing import Dict, List, Any, Optional
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
import sys

# Setup paths
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# Import dependencies
try:
    from evidence_extractor_final import get_evidence_extractor
    from regulation_citation_mapper import get_regulation_mapper
except ImportError:
    # Fallback
    print("⚠️  Could not import extractors, using basic mode")
    get_evidence_extractor = None
    get_regulation_mapper = None

load_dotenv('.env-local')
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


class NSEQueryGenerator:
    """
    Complete NSE-style query generator
    """
    
    def __init__(self):
        """Initialize Query Generator"""
        
        # Initialize extractors
        if get_evidence_extractor:
            self.evidence_extractor = get_evidence_extractor()
        else:
            self.evidence_extractor = None
        
        if get_regulation_mapper:
            self.regulation_mapper = get_regulation_mapper()
        else:
            self.regulation_mapper = None
        
        # NSE tone templates
        self.tone_templates = {
            'MISSING': [
                "It has been observed that {company} has not disclosed",
                "The DRHP does not contain information regarding",
                "{company} has not provided details about"
            ],
            'INSUFFICIENT': [
                "While {company} has provided some information, the following details are missing:",
                "The disclosure is incomplete as it lacks:",
                "The DRHP mentions {quote}, however, the following information is missing:"
            ],
            'UNCLEAR': [
                "The disclosure regarding {topic} is ambiguous",
                "It is unclear from the DRHP whether",
                "Kindly clarify the following aspects:"
            ]
        }
        
        # Initialize Gemini client if available
        if GEMINI_API_KEY and GEMINI_API_KEY not in ["None", ""]:
            try:
                self.client = genai.Client(api_key=GEMINI_API_KEY)
                models_to_try = [
                "gemini-2.5-flash-lite",   # 4K RPM - BEST
                "gemini-2.0-flash-lite",   # 4K RPM
                "gemini-2.0-flash",        # 2K RPM
                "gemini-2.5-flash",        # 1K RPM
                ]
                
                self.model_name = None
                for model in models_to_try:
                    try:
                        self.client.models.generate_content(
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
                
                print(f"✅ NSEQueryGenerator initialized with {self.model_name}")
            except Exception as e:
                print(f"⚠️  Gemini API unavailable: {e}")
                self.client = None
                self.model_name = None
        else:
            self.client = None
            self.model_name = None
            print(f"⚠️  NSEQueryGenerator in TEMPLATE MODE (no API key)")
    
    def extract_company_context(self, drhp_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract company-specific information
        """
        
        context = {
            'company_name': None,
            'industry': None,
            'key_figures': [],
            'key_people': [],
            'locations': []
        }
        
        # Get first pages
        first_pages_text = ""
        for chunk in drhp_chunks[:15]:
            first_pages_text += chunk.get('text', '') + "\n"
        
        # Extract company name
        company_patterns = [
            r'([A-Z][A-Za-z\s&]+(?:Limited|Private Limited|Pvt\.?\s*Ltd\.?|Ltd\.?))',
            r'([A-Z][A-Za-z\s&]+\(India\)\s+(?:Limited|Private Limited))',
        ]
        
        for pattern in company_patterns:
            companies = re.findall(pattern, first_pages_text)
            if companies:
                from collections import Counter
                context['company_name'] = Counter(companies).most_common(1)[0][0]
                break
        
        # Extract figures
        if self.evidence_extractor:
            figures = self.evidence_extractor.extract_figures_and_amounts(first_pages_text)
            context['key_figures'] = [f['amount'] for f in figures[:10]]
        
        # Extract names
        if self.evidence_extractor:
            names = self.evidence_extractor.extract_names(first_pages_text)
            context['key_people'] = [n['name'] for n in names[:10]]
        
        return context
    
    def generate_query(
        self,
        compliance_result: Dict[str, Any],
        drhp_chunks: List[Dict[str, Any]],
        company_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate single NSE-style query
        """
        
        # Extract enhanced evidence
        if self.evidence_extractor:
            enhanced_evidence = self.evidence_extractor.extract_context_for_query(
                compliance_result=compliance_result,
                drhp_chunks=drhp_chunks
            )
        else:
            enhanced_evidence = {
                'verbatim_quote': compliance_result.get('evidence', ''),
                'figures_found': [],
                'names_found': [],
                'inconsistencies': []
            }
        
        # Get specific citation
        if self.regulation_mapper:
            specific_citation = self.regulation_mapper.get_specific_citation(
                obligation=compliance_result.get('obligation', ''),
                regulation_type=compliance_result.get('regulation_type', 'ICDR'),
                generic_citation=compliance_result.get('citation', '')
            )
        else:
            specific_citation = compliance_result.get('citation', 'Applicable Regulations')
        
        # Extract details
        status = compliance_result.get('status', 'UNCLEAR')
        obligation = compliance_result.get('obligation', '')
        pages = compliance_result.get('pages', [])
        missing_details = compliance_result.get('missing_details', '')
        verbatim_quote = enhanced_evidence.get('verbatim_quote', '')
        figures = enhanced_evidence.get('figures_found', [])
        names = enhanced_evidence.get('names_found', [])
        inconsistencies = enhanced_evidence.get('inconsistencies', [])
        
        company_name = company_context.get('company_name', 'the Company')
        
        # Generate query using LLM if available
        if self.client and self.model_name:
            query = self._generate_with_llm(
                obligation, status, pages, verbatim_quote,
                missing_details, figures, names, inconsistencies,
                company_name, specific_citation
            )
        else:
            query = self._generate_with_template(
                obligation, status, pages, verbatim_quote,
                missing_details, figures, names, inconsistencies,
                company_name, specific_citation
            )
        
        return query
    
    def _generate_with_llm(
        self, obligation, status, pages, verbatim_quote,
        missing_details, figures, names, inconsistencies,
        company_name, citation
    ) -> Dict[str, Any]:
        """Generate query using Gemini LLM"""
        
        figures_str = ", ".join(figures[:3]) if figures else "None"
        names_str = ", ".join(names[:3]) if names else "None"
        inconsistencies_str = "\n".join([
            f"- {inc['type']} on pages {inc['pages']}"
            for inc in inconsistencies[:2]
        ]) if inconsistencies else "None"
        
        prompt = f"""You are an NSE/BSE compliance officer drafting formal queries for DRHP review.

COMPLIANCE DETAILS:
- Obligation: {obligation}
- Status: {status}
- Company: {company_name}
- Pages: {pages if pages else 'Not found'}
- Regulation: {citation}

EVIDENCE FROM DRHP:
\"\"\"{verbatim_quote}\"\"\"

DATA EXTRACTED:
- Figures: {figures_str}
- Names: {names_str}
- Cross-page issues: {inconsistencies_str}

MISSING DETAILS:
{missing_details if missing_details else 'N/A'}

TASK: Generate an NSE-style compliance query in this EXACT format:

[Title - Brief topic]
On page [X], [observation with actual quote]. [Detailed explanation]. [What's missing or unclear].

Recommendation: Kindly [specific action].

Regulation Ref: {citation}

[Severity]: Page [X]

CRITICAL REQUIREMENTS:
1. MUST start with "On page [X], " (use pages: {pages})
2. For INSUFFICIENT: Quote actual text then say "However, the following information is missing: [list]"
3. For MISSING: "it has been observed that {company_name} has not disclosed [what's missing]"
4. For UNCLEAR: "the DRHP mentions [quote]. Kindly clarify [what needs clarification]"
5. ALWAYS use "Kindly" before action verbs
6. NEVER use: "the document states", "as per the DRHP" - just quote directly
7. Tone: Professional, respectful, specific
8. If cross-page inconsistencies exist, mention them

SEVERITY:
- MISSING + mandatory → Critical
- MISSING + optional → Major
- INSUFFICIENT → Major
- UNCLEAR → Minor

Generate query now:"""

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    max_output_tokens=1000,
                )
            )
            
            query_text = response.text.strip()
            
            # Parse generated query
            return self._parse_query(query_text, status, pages, citation, obligation)
            
        except Exception as e:
            print(f"⚠️  LLM generation failed: {e}, using template")
            return self._generate_with_template(
                obligation, status, pages, verbatim_quote,
                missing_details, figures, names, inconsistencies,
                company_name, citation
            )
    
    def _generate_with_template(
        self, obligation, status, pages, verbatim_quote,
        missing_details, figures, names, inconsistencies,
        company_name, citation
    ) -> Dict[str, Any]:
        """Generate query using templates (fallback)"""
        
        severity = self._determine_severity(status, obligation)
        page_str = pages[0] if pages else "N/A"
        
        # Build observation based on status
        if status == "MISSING":
            observation = f"it has been observed that {company_name} has not disclosed information regarding: {obligation}."
            if missing_details:
                observation += f" The following details are required: {missing_details}"
        
        elif status == "INSUFFICIENT":
            if verbatim_quote:
                short_quote = verbatim_quote[:150] + "..." if len(verbatim_quote) > 150 else verbatim_quote
                observation = f"the DRHP states: \"{short_quote}\". However, the following information is missing: {missing_details}"
            else:
                observation = f"{company_name} has partially disclosed information regarding {obligation}. The following details are missing: {missing_details}"
        
        else:  # UNCLEAR
            if verbatim_quote:
                short_quote = verbatim_quote[:150] + "..." if len(verbatim_quote) > 150 else verbatim_quote
                observation = f"the DRHP mentions: \"{short_quote}\". Kindly clarify the following: {missing_details if missing_details else 'the disclosure requirements'}"
            else:
                observation = f"the disclosure regarding {obligation} is unclear. Kindly provide clarification."
        
        # Add inconsistency note if found
        inconsistency_note = ""
        if inconsistencies:
            inc = inconsistencies[0]
            inconsistency_note = f" Additionally, there appears to be an inconsistency on pages {inc['pages']} regarding the same information."
        
        # Build recommendation
        if status == "MISSING":
            recommendation = f"Kindly provide complete disclosure of {obligation} as per regulatory requirements."
        elif status == "INSUFFICIENT":
            recommendation = f"Kindly provide the missing details to ensure complete compliance."
        else:
            recommendation = f"Kindly clarify the disclosure to ensure it meets regulatory standards."
        
        title = obligation[:70] + "..." if len(obligation) > 70 else obligation
        
        query_text = f"""{title}
On page {page_str}, {observation}{inconsistency_note}

Recommendation: {recommendation}

Regulation Ref: {citation}

{severity}: Page {page_str}"""

        return {
            'title': title,
            'full_query': query_text,
            'page': str(page_str),
            'severity': severity,
            'regulation': citation,
            'status': status,
            'obligation': obligation,
            'verbatim_evidence': verbatim_quote[:200] if verbatim_quote else "",
            'has_inconsistency': len(inconsistencies) > 0
        }
    
    def _parse_query(
        self, query_text: str, status: str, pages: List[int],
        citation: str, obligation: str
    ) -> Dict[str, Any]:
        """Parse LLM-generated query"""
        
        title_match = re.search(r'^(.+?)(?=\nOn page)', query_text, re.MULTILINE)
        page_match = re.search(r'Page\s+(\d+)', query_text)
        severity_match = re.search(r'(Critical|Major|Minor):', query_text)
        regulation_match = re.search(r'Regulation Ref:\s*(.+?)(?=\n|$)', query_text)
        
        return {
            'title': title_match.group(1).strip() if title_match else obligation[:70],
            'full_query': query_text,
            'page': page_match.group(1) if page_match else (str(pages[0]) if pages else "N/A"),
            'severity': severity_match.group(1) if severity_match else self._determine_severity(status, obligation),
            'regulation': regulation_match.group(1).strip() if regulation_match else citation,
            'status': status,
            'obligation': obligation
        }
    
    def _determine_severity(self, status: str, obligation: str) -> str:
        """Determine severity level"""
        
        critical_keywords = [
            'director', 'promoter', 'financial statement', 'auditor',
            'fraud', 'litigation', 'din', 'board meeting', 'kmp'
        ]
        
        obligation_lower = obligation.lower()
        
        if status == 'MISSING':
            if any(kw in obligation_lower for kw in critical_keywords):
                return 'Critical'
            return 'Major'
        elif status == 'INSUFFICIENT':
            return 'Major'
        else:
            return 'Minor'
    
    def generate_batch_queries(
        self,
        compliance_results: List[Dict[str, Any]],
        drhp_chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate queries for multiple results - SORTED BY PAGE
        """
        
        print(f"\n{'='*80}")
        print(f"📝 GENERATING NSE-STYLE QUERIES")
        print(f"{'='*80}")
        print(f"   Total Results: {len(compliance_results)}")
        
        # Extract company context once
        company_context = self.extract_company_context(drhp_chunks)
        print(f"   Company: {company_context.get('company_name', 'Not identified')}")
        
        # Generate queries
        queries = []
        for i, result in enumerate(compliance_results, 1):
            print(f"   [{i}/{len(compliance_results)}] Processing...")
            
            query = self.generate_query(
                compliance_result=result,
                drhp_chunks=drhp_chunks,
                company_context=company_context
            )
            
            queries.append(query)
        
        # ISSUE #4: SORT BY PAGE NUMBER
        queries_sorted = self.sort_queries_by_page(queries)
        
        print(f"\n{'='*80}")
        print(f"✅ Generated {len(queries_sorted)} queries (sorted by page)")
        print(f"{'='*80}\n")
        
        return queries_sorted
    
    def sort_queries_by_page(
        self,
        queries: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Sort queries by page number (Issue #4)
        """
        
        def get_page_number(query):
            try:
                return int(query.get('page', 9999))
            except:
                return 9999
        
        return sorted(queries, key=get_page_number)
    
    def format_queries_by_page(
        self,
        queries: List[Dict[str, Any]]
    ) -> Dict[int, List[Dict[str, Any]]]:
        """
        Group queries by page for display
        """
        
        by_page = {}
        for query in queries:
            try:
                page_num = int(query.get('page', 9999))
            except:
                page_num = 9999
            
            if page_num not in by_page:
                by_page[page_num] = []
            
            by_page[page_num].append(query)
        
        return dict(sorted(by_page.items()))


def get_nse_query_generator():
    """Factory function"""
    return NSEQueryGenerator()


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """Test Complete Query Generator"""
    
    print("="*80)
    print("🧪 TESTING COMPLETE NSE QUERY GENERATOR")
    print("="*80)
    
    mock_chunks = [
        {
            'page': 145,
            'page_number': 145,
            'text': 'Eco Fuel Systems (India) Limited is engaged in manufacturing. Our revenue for FY2024 was ₹125.50 crores.'
        },
        {
            'page': 146,
            'page_number': 146,
            'text': 'KEY MANAGERIAL PERSONNEL: Mr. Vijay Patel - MD (DIN: 12345678), Ms. Priya Shah - CFO (DIN: 87654321), Mr. Rahul Verma - Company Secretary (Membership No: ACS12345).'
        },
        {
            'page': 147,
            'page_number': 147,
            'text': 'FINANCIAL HIGHLIGHTS: Revenue from operations ₹125.5 crores in FY2024. EBITDA margin: 15.8%.'
        }
    ]
    
    mock_results = [
        {
            'obligation': 'Details of Key Managerial Personnel with DIN numbers must be disclosed',
            'status': 'PRESENT',
            'evidence': 'KMP details provided',
            'missing_details': '',
            'pages': [146],
            'citation': 'ICDR_REG_403',
            'regulation_type': 'ICDR',
            'confidence': 0.9
        },
        {
            'obligation': 'Top 10 customers with percentage of sales',
            'status': 'MISSING',
            'evidence': '',
            'missing_details': 'Customer names, sales percentages for last 3 years',
            'pages': [],
            'citation': 'General',
            'regulation_type': 'ICDR',
            'confidence': 0.95
        },
        {
            'obligation': 'Revenue bifurcation by geography',
            'status': 'INSUFFICIENT',
            'evidence': 'Revenue mentioned but no geographic split',
            'missing_details': 'State-wise domestic revenue, country-wise export revenue',
            'pages': [147],
            'citation': 'ICDR_REG_32',
            'regulation_type': 'ICDR',
            'confidence': 0.8
        }
    ]
    
    generator = get_nse_query_generator()
    
    print("\n" + "="*80)
    print("Generating Batch Queries...")
    print("="*80)
    
    queries = generator.generate_batch_queries(mock_results, mock_chunks)
    
    print("\n" + "="*80)
    print("GENERATED QUERIES (Sorted by Page):")
    print("="*80)
    
    for i, query in enumerate(queries, 1):
        print(f"\n[Query {i}] Page {query['page']} - {query['severity']}")
        print("-" * 80)
        print(query['full_query'])
        print("-" * 80)
    
    print("\n" + "="*80)
    print("✅ Complete Query Generator Test Complete!")
    print("="*80)
