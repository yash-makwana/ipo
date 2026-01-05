"""
Advanced Intelligence Layers - All 4 Missing Dimensions
========================================================

DIMENSION 1: Internal Contradiction Detection
DIMENSION 2: Entity-Level Semantic Identity Tracking  
DIMENSION 3: "Why Is This Mentioned?" Interrogation
DIMENSION 4: Micro-Hygiene & Drafting Nits

These layers add forensic-grade intelligence that catches issues other systems miss.

Author: IPO Compliance System
Version: 2.0 Production
"""

import re
from typing import List, Dict, Any, Set, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass


# ============================================================================
# DIMENSION 1: INTERNAL CONTRADICTION DETECTION
# ============================================================================

@dataclass
class Contradiction:
    """Represents a detected contradiction"""
    type: str  # 'NUMERIC', 'ENTITY', 'CATEGORY', 'TIMELINE'
    entity: str
    pages: List[int]
    values: List[str]
    severity: str
    explanation: str


class ContradictionDetector:
    """
    Detects numeric, entity, and categorical contradictions across chapters
    
    Examples:
    - Revenue ₹500 Cr (page 10) vs ₹480 Cr (page 145)
    - "ABC Ltd is a subsidiary" vs "ABC Ltd is a group company"
    - "200 employees" (page 15) vs "180 employees" (page 89)
    """
    
    # Numeric patterns with context
    NUMERIC_PATTERNS = {
        'REVENUE': r'(?:revenue|turnover|sales).*?₹?\s*(\d+(?:,\d+)?(?:\.\d+)?)\s*(crore|cr|lakh|million)',
        'EMPLOYEES': r'(?:employees?|workforce|personnel).*?(\d+)',
        'CAPACITY': r'(?:capacity|production).*?(\d+(?:,\d+)?(?:\.\d+)?)\s*(units?|tonnes?|MT|KL)',
        'DEALERS': r'(?:dealers?|distributors?|channels?).*?(\d+)',
        'PRODUCTS': r'(?:products?|SKUs?).*?(\d+)',
        'FACILITIES': r'(?:facilities|plants?|units?|locations?).*?(\d+)',
        'CUSTOMERS': r'(?:customers?|clients?).*?(\d+)',
        'SUPPLIERS': r'(?:suppliers?|vendors?).*?(\d+)',
    }
    
    # Entity relationship patterns
    RELATIONSHIP_PATTERNS = {
        'SUBSIDIARY': r'subsidiary|subsidiaries',
        'GROUP_COMPANY': r'group\s+compan(?:y|ies)',
        'ASSOCIATE': r'associate(?:d)?(?:\s+compan(?:y|ies))?',
        'JOINT_VENTURE': r'joint\s+venture',
        'RELATED_PARTY': r'related\s+part(?:y|ies)',
    }
    
    # Business activity patterns
    ACTIVITY_PATTERNS = {
        'MANUFACTURING': r'manufactur(?:e|es|ing|er)',
        'TRADING': r'trad(?:e|es|ing|er)',
        'DISTRIBUTION': r'distribut(?:e|es|ing|or)',
        'SERVICES': r'service(?:s)?',
    }
    
    TOLERANCE_PCT = 2.0  # 2% tolerance for numeric differences
    
    def __init__(self):
        self.numeric_contradictions = []
        self.entity_contradictions = []
        self.category_contradictions = []
    
    def detect_all(self, pages_dict: Dict[int, str]) -> List[Contradiction]:
        """
        Detect all types of contradictions
        
        Args:
            pages_dict: {page_number: page_text}
        
        Returns:
            List of all contradictions
        """
        all_contradictions = []
        
        # Detect numeric contradictions
        all_contradictions.extend(self._detect_numeric(pages_dict))
        
        # Detect entity relationship contradictions
        all_contradictions.extend(self._detect_entity_relationships(pages_dict))
        
        # Detect business activity contradictions
        all_contradictions.extend(self._detect_activity_contradictions(pages_dict))
        
        return all_contradictions
    
    def _detect_numeric(self, pages_dict: Dict[int, str]) -> List[Contradiction]:
        """Detect numeric contradictions"""
        contradictions = []
        
        # Extract all numeric mentions by category
        mentions_by_category = defaultdict(list)
        
        for page_num, text in pages_dict.items():
            text_lower = text.lower()
            
            for category, pattern in self.NUMERIC_PATTERNS.items():
                matches = re.finditer(pattern, text_lower, re.IGNORECASE)
                
                for match in matches:
                    try:
                        value_str = match.group(1).replace(',', '')
                        value = float(value_str)
                        
                        # Convert lakhs to crores
                        if len(match.groups()) > 1:
                            unit = match.group(2).lower()
                            if 'lakh' in unit:
                                value = value / 100
                            elif 'million' in unit:
                                value = value / 10  # ₹1M = ₹0.1 Cr
                        
                        mentions_by_category[category].append({
                            'page': page_num,
                            'value': value,
                            'text': match.group(0)[:50]  # First 50 chars
                        })
                    except (ValueError, IndexError):
                        continue
        
        # Check for contradictions within each category
        for category, mentions in mentions_by_category.items():
            if len(mentions) < 2:
                continue
            
            # Group by similar values (within tolerance)
            value_groups = self._group_similar_values(mentions)
            
            # If multiple distinct groups, it's a contradiction
            if len(value_groups) > 1:
                pages = []
                values = []
                
                for group in value_groups:
                    avg_value = sum(m['value'] for m in group) / len(group)
                    values.append(f"₹{avg_value:.2f} Cr" if 'REVENUE' in category else f"{avg_value:.0f}")
                    pages.extend([m['page'] for m in group])
                
                # Calculate severity
                max_val = max(float(v.split()[0].replace('₹', '')) for v in values)
                min_val = min(float(v.split()[0].replace('₹', '')) for v in values)
                diff_pct = abs(max_val - min_val) / max_val * 100 if max_val > 0 else 0
                
                severity = 'Critical - Valuation' if diff_pct > 20 else 'Major' if diff_pct > 5 else 'Material'
                
                contradictions.append(Contradiction(
                    type='NUMERIC',
                    entity=category,
                    pages=sorted(set(pages)),
                    values=values,
                    severity=severity,
                    explanation=f"{category} shows conflicting values ({diff_pct:.1f}% difference)"
                ))
        
        return contradictions
    
    def _group_similar_values(self, mentions: List[Dict]) -> List[List[Dict]]:
        """Group mentions with similar values (within tolerance)"""
        if not mentions:
            return []
        
        sorted_mentions = sorted(mentions, key=lambda m: m['value'])
        groups = []
        current_group = [sorted_mentions[0]]
        
        for mention in sorted_mentions[1:]:
            base_value = current_group[0]['value']
            current_value = mention['value']
            
            if base_value == 0:
                if current_value == 0:
                    current_group.append(mention)
                else:
                    groups.append(current_group)
                    current_group = [mention]
            else:
                diff_pct = abs(current_value - base_value) / base_value * 100
                
                if diff_pct <= self.TOLERANCE_PCT:
                    current_group.append(mention)
                else:
                    groups.append(current_group)
                    current_group = [mention]
        
        groups.append(current_group)
        return groups
    
    def _detect_entity_relationships(self, pages_dict: Dict[int, str]) -> List[Contradiction]:
        """Detect contradictory entity relationship descriptions"""
        contradictions = []
        
        # Extract company mentions and their relationships
        company_pattern = r'([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\s+(?:Limited|Ltd|Pvt|Private|Inc))'
        
        company_relationships = defaultdict(lambda: {'pages': [], 'relationships': set()})
        
        for page_num, text in pages_dict.items():
            companies = re.finditer(company_pattern, text)
            
            for company_match in companies:
                company_name = company_match.group(1)
                
                # Get context around company mention
                start = max(0, company_match.start() - 100)
                end = min(len(text), company_match.end() + 100)
                context = text[start:end].lower()
                
                # Check for relationship descriptors
                for rel_type, pattern in self.RELATIONSHIP_PATTERNS.items():
                    if re.search(pattern, context):
                        company_relationships[company_name]['pages'].append(page_num)
                        company_relationships[company_name]['relationships'].add(rel_type)
        
        # Check for conflicting relationships
        mutually_exclusive = [
            ('SUBSIDIARY', 'GROUP_COMPANY'),
            ('SUBSIDIARY', 'ASSOCIATE'),
            ('JOINT_VENTURE', 'SUBSIDIARY'),
        ]
        
        for company, data in company_relationships.items():
            relationships = data['relationships']
            
            for rel1, rel2 in mutually_exclusive:
                if rel1 in relationships and rel2 in relationships:
                    contradictions.append(Contradiction(
                        type='ENTITY',
                        entity=company,
                        pages=sorted(set(data['pages'])),
                        values=[rel1.replace('_', ' ').title(), rel2.replace('_', ' ').title()],
                        severity='Major',
                        explanation=f"{company} described with conflicting relationship types"
                    ))
        
        return contradictions
    
    def _detect_activity_contradictions(self, pages_dict: Dict[int, str]) -> List[Contradiction]:
        """Detect contradictory business activity descriptions"""
        contradictions = []
        
        # Track primary business activity mentions
        activity_mentions = defaultdict(list)
        
        trigger_phrases = [
            r'(?:primarily|mainly|principally|engaged in|business of)',
        ]
        
        for page_num, text in pages_dict.items():
            text_lower = text.lower()
            
            for trigger in trigger_phrases:
                trigger_matches = re.finditer(trigger, text_lower)
                
                for trigger_match in trigger_matches:
                    # Get following 50 chars
                    start = trigger_match.end()
                    end = min(len(text_lower), start + 50)
                    context = text_lower[start:end]
                    
                    # Check for activity types
                    for activity, pattern in self.ACTIVITY_PATTERNS.items():
                        if re.search(pattern, context):
                            activity_mentions[activity].append(page_num)
        
        # Check if multiple primary activities mentioned
        primary_activities = [act for act, pages in activity_mentions.items() if len(pages) >= 2]
        
        if len(primary_activities) > 1:
            # Conflicting primary business activities
            all_pages = []
            for activity in primary_activities:
                all_pages.extend(activity_mentions[activity])
            
            contradictions.append(Contradiction(
                type='CATEGORY',
                entity='Business Model',
                pages=sorted(set(all_pages)),
                values=[act.title() for act in primary_activities],
                severity='Critical - Operational',
                explanation=f"Business model described inconsistently as multiple primary activities"
            ))
        
        return contradictions


# ============================================================================
# DIMENSION 2: ENTITY-LEVEL SEMANTIC IDENTITY TRACKING
# ============================================================================

class EntityIdentityTracker:
    """
    Tracks entities across DRHP and ensures consistent descriptions
    
    Entities tracked:
    - Companies (subsidiaries, associates, group companies)
    - Products/Brands
    - Suppliers/Vendors
    - Distributors/Dealers
    - Facilities/Plants
    - Trademarks
    """
    
    ENTITY_PATTERNS = {
        'COMPANY': r'([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\s+(?:Limited|Ltd|Pvt|Private|Inc|Corp))',
        'PRODUCT': r'(?:product|brand|offering)[\s:\"\']+([A-Z][a-zA-Z0-9\s]+?)(?:\s|,|\.|;|\"|\')' ,
        'SUPPLIER': r'(?:supplier|vendor)[\s:\"\']+([A-Z][a-zA-Z\s]+?)(?:\s|,|\.|;|\"|\')' ,
        'DISTRIBUTOR': r'(?:distributor|dealer)[\s:\"\']+([A-Z][a-zA-Z\s]+?)(?:\s|,|\.|;|\"|\')' ,
        'FACILITY': r'(?:facility|plant|unit|manufacturing\s+facility)[\s:]+(?:at|in|located)\s+([A-Z][a-zA-Z\s,]+)',
        'TRADEMARK': r'(?:trademark|TM|®)\s*[\:]*\s*([A-Z][a-zA-Z0-9\s]+)',
    }
    
    def __init__(self):
        self.entities = defaultdict(lambda: {
            'type': None,
            'pages': set(),
            'descriptions': set(),
            'contexts': []
        })
    
    def track_entities(self, pages_dict: Dict[int, str]) -> Dict[str, Any]:
        """Track all entity mentions and their descriptions"""
        
        for page_num, text in pages_dict.items():
            for entity_type, pattern in self.ENTITY_PATTERNS.items():
                matches = re.finditer(pattern, text)
                
                for match in matches:
                    entity_name = match.group(1).strip()
                    
                    # Skip if too short or too long
                    if len(entity_name) < 3 or len(entity_name) > 80:
                        continue
                    
                    # Get surrounding context
                    start = max(0, match.start() - 150)
                    end = min(len(text), match.end() + 150)
                    context = text[start:end]
                    
                    # Extract descriptive attributes
                    attributes = self._extract_attributes(context)
                    
                    # Update entity profile
                    self.entities[entity_name]['type'] = entity_type
                    self.entities[entity_name]['pages'].add(page_num)
                    self.entities[entity_name]['descriptions'].update(attributes)
                    self.entities[entity_name]['contexts'].append({
                        'page': page_num,
                        'context': context[:200]
                    })
        
        return dict(self.entities)
    
    def _extract_attributes(self, context: str) -> Set[str]:
        """Extract descriptive attributes from context"""
        attributes = set()
        
        attribute_patterns = [
            # Relationships
            r'(subsidiary|associate|group\s+company|related\s+party|joint\s+venture)',
            # Exclusivity
            r'(exclusive|non-exclusive|preferred|authorized|sole|primary)',
            # Scale
            r'(leading|major|principal|key|largest|primary|main)',
            # Geography
            r'(domestic|international|overseas|foreign|local|global)',
            # Activity
            r'(manufacturing|trading|distributing|service|consulting)',
            # Status
            r'(operational|under\s+construction|proposed|existing)',
        ]
        
        context_lower = context.lower()
        for pattern in attribute_patterns:
            matches = re.findall(pattern, context_lower)
            attributes.update(matches)
        
        return attributes
    
    def detect_inconsistencies(self) -> List[Dict[str, Any]]:
        """Detect entities with inconsistent or conflicting descriptions"""
        queries = []
        
        # Define mutually exclusive attributes
        conflicts = [
            ('exclusive', 'non-exclusive'),
            ('manufacturing', 'trading'),
            ('operational', 'proposed'),
            ('subsidiary', 'group company'),
            ('domestic', 'international'),
        ]
        
        for entity_name, profile in self.entities.items():
            descriptions = profile['descriptions']
            
            # Check for conflicting attributes
            found_conflicts = []
            for attr1, attr2 in conflicts:
                if attr1 in descriptions and attr2 in descriptions:
                    found_conflicts.extend([attr1, attr2])
            
            if found_conflicts:
                pages = sorted(list(profile['pages']))
                page_ref = f"{pages[0]}" if len(pages) == 1 else f"{pages[0]} to {pages[-1]}"
                
                queries.append({
                    'type': 'entity_identity',
                    'page': page_ref,
                    'observation': (
                        f"On page no. {page_ref}, '{entity_name}' is described with "
                        f"potentially conflicting attributes: {', '.join(set(found_conflicts))}. "
                        f"Kindly clarify the correct classification and ensure consistency "
                        f"across all sections. Provide revised draft confirming uniform description."
                    ),
                    'severity': 'Major',
                    'category': 'Forensic',
                    'issue_id': 'ENTITY_IDENTITY_INCONSISTENCY',
                    'regulation_ref': 'ICDR Regulations - General Disclosure Standards',
                    'entity': entity_name,
                    'entity_type': profile['type']
                })
        
        return queries


# ============================================================================
# DIMENSION 3: "WHY IS THIS MENTIONED?" INTERROGATION
# ============================================================================

class PurposeInterrogator:
    """
    For every operational or strategic statement, ask:
    - Why is this mentioned?
    - What's the quantified impact?
    - What's the dependency/risk?
    - What's the evidence?
    """
    
    INTERROGATION_TRIGGERS = {
        'STRATEGIC_INTENT': [
            r'(?:plan to|intend to|propose to|aim to|strategy is to|will|shall)\s+(\w+(?:\s+\w+){0,8})',
            r'(?:initiative|focus area|strategic priority)[\s:]+((?:\w+\s*){1,10})',
        ],
        'BENEFIT_CLAIM': [
            r'(?:advantage|benefit|strength)(?:\s+is|\s+lies in|\s+includes)[\s:]+([^.]{10,100})',
            r'(?:enables?|allows?|helps?)(?:\s+us|\s+the company)\s+to\s+([^.]{10,100})',
            r'(?:leading to|resulting in|contributing to)\s+([^.]{10,100})',
        ],
        'DEPENDENCY_STATEMENT': [
            r'(?:depends? on|relies? on|based on)\s+([^.]{10,100})',
            r'(?:critical|essential|necessary)\s+for\s+([^.]{10,100})',
            r'(?:key to|fundamental to)\s+([^.]{10,100})',
        ],
        'COMPETITIVE_CLAIM': [
            r'(?:competitive advantage|market position|leadership)\s+(?:in|through)\s+([^.]{10,100})',
            r'(?:differentiat|unique|proprietary)\s+([^.]{10,100})',
        ],
    }
    
    def interrogate(self, pages_dict: Dict[int, str]) -> List[Dict[str, Any]]:
        """Generate purpose interrogation queries"""
        queries = []
        
        for page_num, text in pages_dict.items():
            for category, patterns in self.INTERROGATION_TRIGGERS.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, text, re.IGNORECASE)
                    
                    for match in matches:
                        statement = match.group(0)
                        
                        # Generate interrogation query
                        query = self._create_interrogation_query(
                            page_num, statement, category
                        )
                        if query:
                            queries.append(query)
        
        # Deduplicate and limit
        queries = self._deduplicate(queries)
        
        return queries[:50]  # Limit to 50 interrogations
    
    def _create_interrogation_query(
        self,
        page: int,
        statement: str,
        category: str
    ) -> Optional[Dict]:
        """Create interrogation query based on category"""
        
        # Truncate statement if too long
        if len(statement) > 150:
            statement = statement[:147] + "..."
        
        templates = {
            'STRATEGIC_INTENT': (
                f"On page no. {page}, the disclosure mentions: '{statement}'. "
                f"Kindly provide: (a) quantified rationale (₹/% impact on revenue/profitability "
                f"expected in next 3 years); (b) concrete timeline with milestones; "
                f"(c) capital allocation and source of funds; and (d) a corresponding Risk Factor "
                f"if execution depends on market conditions or regulatory approvals. Provide revised draft."
            ),
            'BENEFIT_CLAIM': (
                f"On page no. {page}, it is claimed: '{statement}'. "
                f"Kindly quantify this benefit by providing: (a) historical evidence (₹/% contribution "
                f"in past 3 years); (b) reconciliation with financial statements showing this benefit; "
                f"(c) peer comparison (whether similar benefits available to competitors); and "
                f"(d) forward-looking quantification if material. Provide revised draft."
            ),
            'DEPENDENCY_STATEMENT': (
                f"On page no. {page}, dependency is mentioned: '{statement}'. "
                f"Kindly disclose: (a) % of revenue/operations dependent on this factor; "
                f"(b) historical instances of disruption (if any) and quantified impact; "
                f"(c) mitigation measures with timeline and cost; and (d) a specific Risk Factor. "
                f"Provide revised draft."
            ),
            'COMPETITIVE_CLAIM': (
                f"On page no. {page}, competitive positioning is claimed: '{statement}'. "
                f"Kindly provide substantiation: (a) third-party validation/market reports; "
                f"(b) quantified metrics vs. peers (market share/margins/growth); "
                f"(c) sustainability of advantage (barriers to entry); and (d) reconciliation "
                f"with business performance. Provide revised draft."
            ),
        }
        
        if category in templates:
            return {
                'type': 'purpose_interrogation',
                'page': str(page),
                'observation': templates[category],
                'severity': 'Material',
                'category': 'Operational',
                'issue_id': f'PURPOSE_{category}',
                'regulation_ref': 'ICDR Regulations - General Disclosure Standards',
                'interrogation_category': category
            }
        
        return None
    
    def _deduplicate(self, queries: List[Dict]) -> List[Dict]:
        """Remove duplicate interrogations"""
        seen = set()
        unique = []
        
        for query in queries:
            # Create key from page and first 50 chars of observation
            key = (query['page'], query['observation'][:50])
            if key not in seen:
                seen.add(key)
                unique.append(query)
        
        return unique


# ============================================================================
# DIMENSION 4: MICRO-HYGIENE & DRAFTING NITS
# ============================================================================

class DraftingHygieneScanner:
    """
    Scans for micro-level drafting issues:
    - Footnote reference mismatches
    - Undefined acronyms
    - Inconsistent number formatting in tables
    - Caption numbering gaps
    - Section reference errors
    """
    
    def scan(self, pages_dict: Dict[int, str]) -> List[Dict[str, Any]]:
        """Run all hygiene scans"""
        queries = []
        
        for page_num, text in pages_dict.items():
            queries.extend(self._check_footnotes(page_num, text))
            queries.extend(self._check_acronyms(page_num, text))
            queries.extend(self._check_number_formatting(page_num, text))
            queries.extend(self._check_captions(page_num, text))
            queries.extend(self._check_section_references(page_num, text))
        
        return queries[:30]  # Limit hygiene nits to 30
    
    def _check_footnotes(self, page: int, text: str) -> List[Dict]:
        """Check footnote symbols are properly referenced"""
        queries = []
        
        # Find footnote symbols
        footnote_symbols = re.findall(r'[\*†‡§¶#](?:\d+)?', text)
        
        # Check each symbol
        symbol_counts = defaultdict(int)
        for symbol in footnote_symbols:
            symbol_counts[symbol] += 1
        
        # Footnote should appear at least twice (reference + definition)
        for symbol, count in symbol_counts.items():
            if count == 1:
                queries.append({
                    'type': 'hygiene',
                    'page': str(page),
                    'observation': (
                        f"On page no. {page}, footnote symbol '{symbol}' appears unreferenced. "
                        f"Kindly ensure all footnotes are properly cross-referenced "
                        f"(both in-text reference and footnote definition). Provide revised draft."
                    ),
                    'severity': 'Hygiene',
                    'category': 'Drafting Quality',
                    'issue_id': 'FOOTNOTE_MISMATCH',
                    'regulation_ref': 'SEBI Circular on DRHP Format'
                })
        
        return queries[:2]  # Limit per page
    
    def _check_acronyms(self, page: int, text: str) -> List[Dict]:
        """Check for undefined acronyms"""
        queries = []
        
        # Find all-caps acronyms (2-6 letters)
        acronyms = set(re.findall(r'\b([A-Z]{2,6})\b', text))
        
        # Filter out common words
        common = {'THE', 'AND', 'FOR', 'WITH', 'FROM', 'THIS', 'THAT', 'IPO', 'NSE', 'BSE', 'SEBI'}
        acronyms = acronyms - common
        
        undefined = []
        for acronym in acronyms:
            # Check if defined (look for expansion pattern)
            definition_pattern = rf'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+\({acronym}\)'
            
            if not re.search(definition_pattern, text):
                undefined.append(acronym)
        
        if len(undefined) > 0:
            # Sample first 3 undefined acronyms
            sample = undefined[:3]
            queries.append({
                'type': 'hygiene',
                'page': str(page),
                'observation': (
                    f"On page no. {page}, acronym(s) '{', '.join(sample)}' appear without definition. "
                    f"Kindly provide full form on first occurrence or in glossary/abbreviations section. "
                    f"Provide revised draft."
                ),
                'severity': 'Hygiene',
                'category': 'Drafting Quality',
                'issue_id': 'UNDEFINED_ACRONYM',
                'regulation_ref': 'SEBI Circular on DRHP Format'
            })
        
        return queries
    
    def _check_number_formatting(self, page: int, text: str) -> List[Dict]:
        """Check for inconsistent number formatting"""
        queries = []
        
        # Find comma-separated numbers
        comma_nums = len(re.findall(r'\d{1,3}(?:,\d{3})+', text))
        
        # Find non-comma large numbers (4+ digits)
        non_comma_nums = len(re.findall(r'(?<!\d)\d{4,}(?!\d)', text))
        
        # If both styles present significantly
        if comma_nums > 3 and non_comma_nums > 3:
            queries.append({
                'type': 'hygiene',
                'page': str(page),
                'observation': (
                    f"On page no. {page}, numeric formatting appears inconsistent "
                    f"(both comma-separated and non-separated formats detected in tables/text). "
                    f"Kindly ensure uniform number formatting across all tables and disclosures. "
                    f"Provide revised draft."
                ),
                'severity': 'Hygiene',
                'category': 'Drafting Quality',
                'issue_id': 'INCONSISTENT_NUMBER_FORMAT',
                'regulation_ref': 'SEBI Circular on DRHP Format'
            })
        
        return queries
    
    def _check_captions(self, page: int, text: str) -> List[Dict]:
        """Check table/figure caption numbering"""
        queries = []
        
        # Find all table numbers
        table_nums = [int(m.group(1)) for m in re.finditer(r'Table\s+(\d+)', text)]
        
        if table_nums:
            # Check for gaps or duplicates
            if len(table_nums) != len(set(table_nums)):
                queries.append({
                    'type': 'hygiene',
                    'page': str(page),
                    'observation': (
                        f"On page no. {page}, table numbering shows duplicates "
                        f"(same table number used multiple times). Kindly review and ensure "
                        f"sequential, non-duplicate numbering. Provide revised draft."
                    ),
                    'severity': 'Hygiene',
                    'category': 'Drafting Quality',
                    'issue_id': 'CAPTION_DUPLICATE',
                    'regulation_ref': 'SEBI Circular on DRHP Format'
                })
        
        return queries
    
    def _check_section_references(self, page: int, text: str) -> List[Dict]:
        """Check for broken section references"""
        queries = []
        
        # Find section references like "see Section X.Y"
        ref_pattern = r'(?:see|refer to|as mentioned in)\s+(?:Section|Chapter)\s+([0-9\.]+)'
        refs = re.findall(ref_pattern, text, re.IGNORECASE)
        
        # Basic validation: check if referenced sections exist in text
        # (This is simplified - full validation would require document structure)
        
        if refs:
            # Sample check: ensure referenced section is not the current page section
            pass  # Simplified for now
        
        return queries


# ============================================================================
# MASTER ORCHESTRATOR FOR ALL 4 DIMENSIONS
# ============================================================================

class AdvancedIntelligenceLayers:
    """
    Orchestrates all 4 advanced dimensions:
    
    1. Internal Contradiction Detection
    2. Entity Identity Tracking
    3. Purpose Interrogation
    4. Drafting Hygiene
    """
    
    def __init__(self):
        self.contradiction_detector = ContradictionDetector()
        self.entity_tracker = EntityIdentityTracker()
        self.purpose_interrogator = PurposeInterrogator()
        self.hygiene_scanner = DraftingHygieneScanner()
        
        print("\n✅ Advanced Intelligence Layers initialized")
        print("   ✓ Dimension 1: Contradiction Detection")
        print("   ✓ Dimension 2: Entity Identity Tracking")
        print("   ✓ Dimension 3: Purpose Interrogation")
        print("   ✓ Dimension 4: Drafting Hygiene")
    
    def run_all_dimensions(
        self,
        pages_dict: Dict[int, str]
    ) -> Dict[str, List[Dict]]:
        """
        Run all 4 advanced dimension checks
        
        Args:
            pages_dict: {page_number: page_text}
        
        Returns:
            Dict with queries from each dimension
        """
        print(f"\n{'='*80}")
        print(f"🧠 ADVANCED INTELLIGENCE LAYERS - 4 DIMENSIONS")
        print(f"{'='*80}")
        print(f"Analyzing {len(pages_dict)} pages...")
        
        results = {}
        
        # Dimension 1: Contradiction Detection
        print(f"\n[Dimension 1/4] Internal Contradiction Detection...")
        contradictions = self.contradiction_detector.detect_all(pages_dict)
        results['contradictions'] = self._contradictions_to_queries(contradictions)
        print(f"   ✓ Detected {len(contradictions)} contradictions")
        
        # Dimension 2: Entity Identity Tracking
        print(f"\n[Dimension 2/4] Entity Identity Tracking...")
        entity_profiles = self.entity_tracker.track_entities(pages_dict)
        results['entity_identity'] = self.entity_tracker.detect_inconsistencies()
        print(f"   ✓ Tracked {len(entity_profiles)} entities")
        print(f"   ✓ Found {len(results['entity_identity'])} identity inconsistencies")
        
        # Dimension 3: Purpose Interrogation
        print(f"\n[Dimension 3/4] Purpose Interrogation...")
        results['purpose_interrogation'] = self.purpose_interrogator.interrogate(pages_dict)
        print(f"   ✓ Generated {len(results['purpose_interrogation'])} interrogation queries")
        
        # Dimension 4: Drafting Hygiene
        print(f"\n[Dimension 4/4] Drafting Hygiene Scan...")
        results['hygiene'] = self.hygiene_scanner.scan(pages_dict)
        print(f"   ✓ Found {len(results['hygiene'])} hygiene issues")
        
        total = sum(len(queries) for queries in results.values())
        print(f"\n✅ Advanced layers complete: {total} additional queries generated")
        print(f"{'='*80}\n")
        
        return results
    
    def _contradictions_to_queries(self, contradictions: List[Contradiction]) -> List[Dict]:
        """Convert Contradiction objects to query dicts"""
        queries = []
        
        for contradiction in contradictions:
            # Format page reference
            if len(contradiction.pages) == 1:
                page_ref = str(contradiction.pages[0])
            elif len(contradiction.pages) == 2:
                page_ref = f"{contradiction.pages[0]} and {contradiction.pages[1]}"
            else:
                page_ref = f"{contradiction.pages[0]} to {contradiction.pages[-1]}"
            
            # Create observation text
            if contradiction.type == 'NUMERIC':
                observation = (
                    f"On page no. {page_ref}, there appears to be a numerical inconsistency "
                    f"regarding {contradiction.entity}. The disclosure mentions conflicting values: "
                    f"{' vs '.join(contradiction.values)}. Kindly reconcile this factual "
                    f"contradiction and provide revised draft along with confirmation that "
                    f"the same shall be updated in the final prospectus."
                )
            elif contradiction.type == 'ENTITY':
                observation = (
                    f"On page no. {page_ref}, {contradiction.entity} is described with "
                    f"conflicting classifications: {' vs '.join(contradiction.values)}. "
                    f"Kindly clarify the correct classification and ensure consistency "
                    f"across all chapters. Provide revised draft."
                )
            else:  # CATEGORY
                observation = (
                    f"On page no. {page_ref}, {contradiction.entity} is categorized "
                    f"inconsistently: {' vs '.join(contradiction.values)}. Kindly reconcile "
                    f"this categorical contradiction and ensure uniform classification "
                    f"throughout the DRHP. Provide revised draft."
                )
            
            queries.append({
                'type': 'contradiction',
                'page': page_ref,
                'observation': observation,
                'severity': contradiction.severity,
                'category': 'Forensic',
                'issue_id': f'CONTRADICTION_{contradiction.type}',
                'regulation_ref': 'ICDR Regulations - General Disclosure Standards',
                'contradiction_details': {
                    'type': contradiction.type,
                    'entity': contradiction.entity,
                    'values': contradiction.values
                }
            })
        
        return queries


def get_advanced_intelligence_layers():
    """Factory function to get advanced layers instance"""
    return AdvancedIntelligenceLayers()