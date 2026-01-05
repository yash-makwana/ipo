from vertexai.generative_models import GenerativeModel
import json
import os
import re

class QueryClassifier:
    """
    Classifies user queries to determine compliance checking strategy.
    Now includes NSE/Exchange Observation detection!
    """
    
    def __init__(self):
        """
        Initialize QueryClassifier using GCP's default credentials
        (same pattern as ComplianceEngine)
        """
        # ✅ Use GCP default credentials - NO API KEY NEEDED
        self.llm = GenerativeModel('gemini-2.5-pro')
        
        print("✅ QueryClassifier initialized with NSE observation support")
    
    def classify_query(self, user_query, document_chapter):
        """
        Main classification entry point with NSE observation detection
        """
        
        # If no query, do standard compliance check
        if not user_query or user_query.strip() == "":
            return {
                'query_type': 'STANDARD_COMPLIANCE',
                'confidence': 1.0,
                'focus_areas': ['all'],
                'should_check': ['all_applicable_requirements'],
                'should_not_check': [],
                'suggested_requirements': []
            }
        
        # ⭐⭐⭐ DETECT NSE OBSERVATION QUERIES ⭐⭐⭐
        if self._is_nse_observation(user_query):
            print(f"🎯 DETECTED: NSE/Exchange Observation!")
            return self.classify_nse_observation(user_query, document_chapter)
        
        # Otherwise, do regular query classification
        return self._classify_regular_query(user_query, document_chapter)
    
    def _is_nse_observation(self, user_query):
        """
        Detect if this is an NSE/BSE observation query
        These have specific patterns that distinguish them from regular queries
        """
        query_lower = user_query.lower()
        
        # Strong indicators of NSE observations
        strong_indicators = [
            'kindly' in query_lower,
            'clarify' in query_lower and ('rhp' in query_lower or 'drhp' in query_lower),
            'provide details' in query_lower and 'confirmation' in query_lower,
            'elaborate' in query_lower and 'page' in query_lower,
            'disclose' in query_lower and 'revised draft' in query_lower,
            'share the revised draft along with' in query_lower,
            'confirmation that the same will be included in the rhp' in query_lower,
            'confirmation that the same will be disclosed in the rhp' in query_lower,
            bool(re.search(r'\b(a|b|c|d|e|f|g|h|i)\)', user_query))  # Observation markers like "a)", "b)"
        ]
        
        # NSE observations typically have multiple indicators
        indicator_count = sum(strong_indicators)
        
        if indicator_count >= 2:
            print(f"   ✓ Found {indicator_count} NSE observation indicators")
            return True
        
        # Additional check: mentions specific page numbers + formal language
        has_page_ref = bool(re.search(r'page\s+\d+', query_lower))
        has_formal_request = any(phrase in query_lower for phrase in [
            'kindly', 'please provide', 'it is mentioned that', 
            'it has been observed', 'w.r.t', 'further,', 'accordingly,'
        ])
        
        if has_page_ref and has_formal_request:
            print(f"   ✓ Found page reference + formal language")
            return True
        
        return False
    
    def classify_nse_observation(self, user_query, document_chapter):
        """
        Special classification for NSE/BSE observations
        These are NOT compliance checks - they're content gap analyses!
        """
        
        print(f"📋 Classifying NSE Observation...")
        
        prompt = f"""You are analyzing an NSE/BSE observation/query about a DRHP chapter.

DOCUMENT CHAPTER: {document_chapter}

NSE OBSERVATION:
{user_query}

TASK: Extract what the exchange is asking for.

Respond ONLY with JSON (no markdown, no backticks):
{{
    "query_type": "NSE_OBSERVATION",
    "observation_type": "ELABORATE|CLARIFY|DISCLOSE_DATA|SUBSTANTIATE|AMEND|PROVIDE_DETAILS",
    "specific_asks": ["list of specific things NSE wants"],
    "page_references": [list of page numbers mentioned as integers],
    "requires_quantitative_data": true or false,
    "requires_source_documents": true or false,
    "requires_draft_revision": true or false,
    "key_terms": ["important terms to search for in document"]
}}

EXAMPLES:

Query: "Kindly elaborate on selling strategy for retailers including sales platform"
Response:
{{
    "query_type": "NSE_OBSERVATION",
    "observation_type": "ELABORATE",
    "specific_asks": [
        "selling strategy for retailers",
        "how company undertakes sales for retailers",
        "sales platform details if any"
    ],
    "page_references": [133],
    "requires_quantitative_data": false,
    "requires_source_documents": false,
    "requires_draft_revision": true,
    "key_terms": ["retailers", "sales strategy", "sales platform", "distribution"]
}}

Query: "Kindly provide number of wholesalers for last 3 FYs"
Response:
{{
    "query_type": "NSE_OBSERVATION",
    "observation_type": "DISCLOSE_DATA",
    "specific_asks": [
        "number of wholesalers in FY 2022",
        "number of wholesalers in FY 2023",
        "number of wholesalers in FY 2024"
    ],
    "page_references": [138],
    "requires_quantitative_data": true,
    "requires_source_documents": false,
    "requires_draft_revision": true,
    "key_terms": ["wholesalers", "distributors", "market network"]
}}

Query: "Provide source for 'rich experienced management team' statement"
Response:
{{
    "query_type": "NSE_OBSERVATION",
    "observation_type": "SUBSTANTIATE",
    "specific_asks": [
        "source document for management team experience claim",
        "justification for 'rich experienced' adjective"
    ],
    "page_references": [137],
    "requires_quantitative_data": false,
    "requires_source_documents": true,
    "requires_draft_revision": true,
    "key_terms": ["management team", "experience", "professional"]
}}

Now analyze the provided observation.
"""
        
        try:
            response = self.llm.generate_content(prompt)
            text = response.text.strip()
            
            # Clean up response
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            
            result = json.loads(text.strip())
            result['confidence'] = 0.95
            
            print(f"   📝 Observation Type: {result.get('observation_type')}")
            print(f"   📋 Specific Asks: {len(result.get('specific_asks', []))} items")
            print(f"   📄 Page References: {result.get('page_references', [])}")
            
            return result
            
        except Exception as e:
            print(f"⚠️  NSE classification failed: {e}")
            
            # Fallback - still mark as NSE observation
            page_numbers = re.findall(r'page\s+(\d+)', user_query.lower())
            
            return {
                'query_type': 'NSE_OBSERVATION',
                'observation_type': 'ELABORATE',
                'specific_asks': [user_query.strip()],
                'page_references': [int(p) for p in page_numbers],
                'requires_quantitative_data': 'number' in user_query.lower() or 'data' in user_query.lower(),
                'requires_source_documents': 'source' in user_query.lower() or 'evidence' in user_query.lower(),
                'requires_draft_revision': True,
                'key_terms': [],
                'confidence': 0.7
            }
    
    def _classify_regular_query(self, user_query, document_chapter):
        """
        Regular query classification (your existing logic)
        """
        
        print(f"🔍 Classifying regular query...")
        
        prompt = f"""You are analyzing a user query about a DRHP compliance check.

DOCUMENT CHAPTER: {document_chapter}

USER QUERY:
{user_query}

TASK: Classify the query intent.

Respond with JSON:
{{
    "query_type": "CONTENT_ENHANCEMENT|FACTUAL_VERIFICATION|SUBSTANTIATION_REQUIRED|PROCEDURAL_COMPLIANCE|DISCLOSURE_ADDITION",
    "focus_areas": ["specific topics to focus on"],
    "should_check": ["list of requirement types to check"],
    "should_not_check": ["list of requirement types to skip"],
    "page_references": [page numbers if mentioned],
    "confidence": 0.0 to 1.0
}}

Query Types:
- CONTENT_ENHANCEMENT: "elaborate", "clarify", "provide details"
- FACTUAL_VERIFICATION: "how many", "what is the rate", "verify data"
- SUBSTANTIATION_REQUIRED: "provide source", "evidence", "justify"
- PROCEDURAL_COMPLIANCE: "filed with Board", "Schedule III fees"
- DISCLOSURE_ADDITION: "disclose trend", "include information"
"""
        
        try:
            response = self.llm.generate_content(prompt)
            text = response.text.strip()
            
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            
            result = json.loads(text.strip())
            return result
            
        except Exception as e:
            print(f"⚠️  Regular classification failed: {e}")
            return {
                'query_type': 'CONTENT_ENHANCEMENT',
                'focus_areas': ['all'],
                'should_check': ['all'],
                'should_not_check': [],
                'page_references': [],
                'confidence': 0.5
            }

_query_classifier = None

def get_query_classifier():
    """Get or create the global QueryClassifier instance"""
    global _query_classifier
    if _query_classifier is None:
        _query_classifier = QueryClassifier()
    return _query_classifier