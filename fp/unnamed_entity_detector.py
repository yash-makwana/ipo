"""
Unnamed Entity Detector - FIXES MISS #3
========================================
Detects when document refers to entities without naming them
and generates NSE queries demanding specific names.

This fixes the "Chinese distributor name" type misses.

Author: IPO Compliance System - Accuracy Enhancement
Date: January 2026
"""

import re
from typing import Dict, List, Tuple


class UnnamedEntityDetector:
    """
    Detects unnamed entities and generates NSE queries
    
    Catches patterns like:
    - "a Chinese distributor" (no name)
    - "one of our suppliers" (no name)
    - "a major customer" (no name)
    - "foreign manufacturer" (no name)
    """
    
    def __init__(self):
        """Initialize unnamed entity detector"""
        
        # Patterns for unnamed entities
        self.unnamed_patterns = [
            # Distributors
            (r'(?:a|an|one of our|the)\s+(?:\w+\s+)?distributor(?:s)?(?:\s+(?:in|from|based in)\s+(\w+))?', 
             'distributor'),
            
            # Suppliers
            (r'(?:a|an|one of our|the)\s+(?:\w+\s+)?supplier(?:s)?(?:\s+(?:in|from|based in)\s+(\w+))?',
             'supplier'),
            
            # Customers
            (r'(?:a|an|one of our|major|key)\s+customer(?:s)?(?:\s+(?:in|from|based in)\s+(\w+))?',
             'customer'),
            
            # Manufacturers
            (r'(?:a|an|foreign|overseas|international)\s+manufacturer(?:s)?(?:\s+(?:in|from|based in)\s+(\w+))?',
             'manufacturer'),
            
            # Generic business partners
            (r'(?:a|an|our)\s+(?:\w+\s+)?(?:partner|vendor|contractor|consultant|advisor)(?:\s+(?:in|from|based in)\s+(\w+))?',
             'business partner'),
            
            # Technology providers
            (r'(?:a|an|the)\s+(?:\w+\s+)?(?:technology provider|licensor)(?:\s+(?:in|from|based in)\s+(\w+))?',
             'technology provider'),
             
            # Auditors/Consultants
            (r'(?:a|an|reputed)\s+(?:\w+\s+)?(?:auditor|firm|consultancy)(?:\s+(?:in|from|based in)\s+(\w+))?',
             'auditor/consultant'),
             
            # Promoters/Group entities
            (r'(?:certain|reputed)\s+(?:\w+\s+)?(?:promoter|group\s+entity|shareholder)(?:\s+(?:in|from|based in)\s+(\w+))?',
             'promoter/entity')
        ]
        
        # Country/nationality keywords and tax havens
        self.foreign_indicators = [
            'chinese', 'china', 'german', 'germany', 'japanese', 'japan',
            'american', 'usa', 'korean', 'korea', 'taiwan', 'hong kong',
            'singapore', 'foreign', 'international', 'overseas', 'imported',
            'mauritius', 'cayman', 'british virgin islands', 'bvi', 'cyprus', 'dubai', 'uae'
        ]
        
        print("✅ Unnamed Entity Detector initialized")
    
    def detect_unnamed_entities(self, pages_dict: Dict[int, str]) -> List[Dict]:
        """
        Scan document for unnamed entities
        
        Args:
            pages_dict: {page_num: page_text}
        
        Returns:
            List of queries requesting entity names
        """
        
        queries = []
        
        for page_num, text in pages_dict.items():
            
            # Find all unnamed entities on this page
            entities = self._find_unnamed_entities(text, page_num)
            
            for entity in entities:
                query = self._generate_entity_query(entity, page_num)
                queries.append(query)
        
        return queries
    
    def _find_unnamed_entities(
        self, 
        text: str, 
        page_num: int
    ) -> List[Dict]:
        """
        Find unnamed entities in text
        
        Returns:
            [
                {
                    'type': 'distributor',
                    'location': 'China',
                    'context': 'full sentence',
                    'is_foreign': True,
                    'priority': 'high'
                }
            ]
        """
        
        entities = []
        
        for pattern, entity_type in self.unnamed_patterns:
            
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                
                # Extract context (full sentence)
                context = self._extract_sentence(text, match.start())
                
                # Check if named (has capital letter after the entity type)
                # e.g., "distributor ABC Ltd" vs "a distributor"
                is_named = self._is_entity_named(text, match.end())
                
                if not is_named:
                    
                    # Extract location if present
                    # 🔴 FIX: Check if lastindex is not None before comparison
                    location = match.group(1) if match.lastindex and match.lastindex >= 1 else None
                    
                    # Check if foreign
                    is_foreign = self._is_foreign_entity(context)
                    
                    # Priority (foreign entities = high priority)
                    priority = 'high' if is_foreign else 'medium'
                    
                    entities.append({
                        'type': entity_type,
                        'location': location,
                        'context': context,
                        'is_foreign': is_foreign,
                        'priority': priority
                    })
        
        return entities
    
    def _extract_sentence(self, text: str, position: int) -> str:
        """Extract full sentence containing the position"""
        
        # Find sentence boundaries
        before = text[:position]
        after = text[position:]
        
        # Find last period before position
        last_period = before.rfind('.')
        if last_period == -1:
            last_period = 0
        else:
            last_period += 1
        
        # Find next period after position
        next_period = after.find('.')
        if next_period == -1:
            next_period = len(after)
        
        sentence = text[last_period:position + next_period]
        return sentence.strip()
    
    def _is_entity_named(self, text: str, after_position: int) -> bool:
        """
        Check if entity is named (has proper name following)
        
        e.g., "distributor ABC Ltd" → True
        e.g., "a distributor" → False
        """
        
        # Look at next 50 characters
        snippet = text[after_position:after_position + 50]
        
        # Check for capital letters indicating a name
        # Pattern: optional "named"/"called", then capitals
        name_pattern = r'(?:named|called)?\s*([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*(?:\s+(?:Ltd|Limited|Inc|Corp|Co))?)'
        
        match = re.search(name_pattern, snippet)
        
        # But exclude generic capitals like "China", "India"
        if match:
            potential_name = match.group(1)
            # Exclude single-word country names
            if len(potential_name.split()) > 1:
                return True
        
        return False
    
    def _is_foreign_entity(self, context: str) -> bool:
        """Check if entity is foreign based on context"""
        
        context_lower = context.lower()
        
        return any(
            indicator in context_lower
            for indicator in self.foreign_indicators
        )
    
    def _generate_entity_query(self, entity: Dict, page_num: int) -> Dict:
        """Generate NSE-style query requesting entity name"""
        
        entity_type = entity['type']
        location = entity['location']
        is_foreign = entity['is_foreign']
        
        # Build query text
        if location and is_foreign:
            query_text = (
                f"On page {page_num}, the Company mentions {entity_type} "
                f"from {location} without providing the name. "
                f"Kindly provide the complete name of the {entity_type}, "
                f"details of the business arrangement, and the nature of dependency. "
                f"Provide revised draft along with confirmation that the same shall be "
                f"updated in the prospectus."
            )
        elif is_foreign:
            query_text = (
                f"On page {page_num}, the Company mentions a foreign {entity_type} "
                f"without providing the name. "
                f"Kindly provide the complete name of the {entity_type} and "
                f"details of the business arrangement. "
                f"Provide revised draft along with confirmation that the same shall be "
                f"updated in the prospectus."
            )
        else:
            query_text = (
                f"On page {page_num}, the Company mentions {entity_type} "
                f"without providing the name. "
                f"Kindly provide the complete name of the {entity_type}. "
                f"Provide revised draft along with confirmation that the same shall be "
                f"updated in the prospectus."
            )
        
        return {
            'page': str(page_num),
            'text': query_text,
            'type': 'TYPE_UNNAMED_ENTITY',
            'issue_id': f'UNNAMED_{entity_type.upper().replace(" ", "_")}',
            'severity': 'Major' if is_foreign else 'Material',
            'category': 'Disclosure'
        }


def get_unnamed_entity_detector():
    """Factory function"""
    return UnnamedEntityDetector()


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """Test the detector"""
    
    detector = UnnamedEntityDetector()
    
    # Test text
    test_text = """
    The Company sources raw materials from a Chinese distributor based in Shanghai.
    We also work with one of our major suppliers in Germany.
    Our products are sold to a key customer in the automotive sector.
    We have engaged a technology provider for our manufacturing process.
    
    Additionally, we procure from XYZ Limited, a registered supplier in India.
    """
    
    pages_dict = {153: test_text}
    
    queries = detector.detect_unnamed_entities(pages_dict)
    
    print(f"\n🔍 Found {len(queries)} unnamed entity queries:")
    for q in queries:
        print(f"\n[{q['severity']}] {q['text']}")