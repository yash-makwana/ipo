"""
Interpretation & Normalization Layer
=====================================

The MISSING intelligence layer that transforms raw findings into context-aware,
properly calibrated NSE-style queries.

This layer sits between System A (Compliance) and System B (Content Review)
and the final output, providing:

1. Business Model Normalization
2. Disclosure Status Classification
3. Materiality Scoring
4. Query Collision Resolution
5. Severity & Tone Control
6. Section Placement Enforcement

Author: IPO Compliance System
Version: 1.0 Production
"""

from typing import List, Dict, Any, Optional, Tuple
import re


# ============================================================================
# 1️⃣ BUSINESS MODEL NORMALIZER
# ============================================================================

class BusinessModelNormalizer:
    """
    Adjusts queries based on business type and scale
    
    Manufacturing: Capacity, utilities, scrap, logistics
    Services: Attrition, client retention, service metrics
    Trading: Inventory, distributor network, margins
    """
    
    # Define which queries are relevant for each business model
    MANUFACTURING_RELEVANT = {
        'CAPACITY_CERTIFICATION', 'CAPACITY_UTILIZATION', 'UTILITIES_POWER_WATER',
        'OPERATIONAL_SCRAP', 'OWN_VS_CONTRACTUAL_MANUFACTURING', 
        'PROCESS_FLOW_ALIGNMENT', 'QA_INSPECTION_CERT_PROCESS',
        'RAW_MATERIAL_PRICE_VOLATILITY', 'SUPPLIER_CONCENTRATION'
    }
    
    SERVICES_RELEVANT = {
        'ATTRITION_RATE', 'CUSTOMER_CHURN_REPEAT', 'KEY_MAN_DEPENDENCY_RISK',
        'MANAGEMENT_EXPERIENCE_INDIVIDUAL', 'RD_INVESTMENT_DISCLOSURE',
        'BRANDING_INVESTMENT_QUANTIFICATION'
    }
    
    TRADING_RELEVANT = {
        'DISTRIBUTION_NETWORK', 'LOGISTICS_MECHANISM_AUDIT', 
        'SUPPLIER_CONCENTRATION', 'INVENTORY_MANAGEMENT',
        'EXCLUSIVE_DISTRIBUTOR_VERIFICATION', 'COUNTRY_WISE_IMPORT_TABLE'
    }
    
    # Universal queries (apply to all business types)
    UNIVERSAL_QUERIES = {
        'REVENUE_MODEL_EXPLANATION', 'GEOGRAPHIC_REVENUE_SPLIT',
        'DOMESTIC_EXPORT_RECON', 'CSR_BUDGET_EXECUTION',
        'LEASE_STATUS_MANDATORY', 'INSURANCE_AUDIT_MISMATCH',
        'EPF_ESIC_COMPLIANCE_NON_PAYMENT', 'REGULATORY_ACTIONS_HISTORY',
        'LITIGATION_COMPLIANCE_STATUS', 'FINANCIAL_CERTIFICATION_MD',
        'SUPERLATIVE_EVIDENCE', 'MEASUREMENT_UNIT_CONSISTENCY'
    }
    
    def __init__(self):
        self.name = "Business Model Normalizer"
    
    def normalize(self, queries: List[Dict], company_profile: Dict) -> List[Dict]:
        """
        Filter queries based on business model relevance
        
        Args:
            queries: List of query dicts with 'issue_id'
            company_profile: {business_type, revenue, employees}
            
        Returns:
            Filtered list of relevant queries
        """
        business_type = company_profile.get('business_type', '').upper()
        revenue = company_profile.get('revenue', 0)
        
        # Classify business model
        if 'MANUFACTURING' in business_type or 'INDUSTRIAL' in business_type:
            model = 'MANUFACTURING'
        elif 'SERVICE' in business_type or 'CONSULTING' in business_type:
            model = 'SERVICES'
        elif 'TRADING' in business_type or 'DISTRIBUTION' in business_type:
            model = 'TRADING'
        else:
            # Default: allow all queries if uncertain
            return queries
        
        relevant_issues = self.UNIVERSAL_QUERIES.copy()
        
        if model == 'MANUFACTURING':
            relevant_issues.update(self.MANUFACTURING_RELEVANT)
        elif model == 'SERVICES':
            relevant_issues.update(self.SERVICES_RELEVANT)
        elif model == 'TRADING':
            relevant_issues.update(self.TRADING_RELEVANT)
        
        # Filter queries
        filtered = []
        skipped = 0
        
        for query in queries:
            # Preserve any locked expectation queries
            if query.get('locked'):
                filtered.append(query)
                continue
            issue_id = query.get('issue_id', '')
            
            if issue_id in relevant_issues or not issue_id:
                # Keep universal queries or queries without issue_id
                filtered.append(query)
            else:
                skipped += 1
        
        if skipped > 0:
            print(f"   [Normalizer] Filtered {skipped} business-irrelevant queries ({model} model)")
        
        return filtered


# ============================================================================
# 2️⃣ DISCLOSURE STATUS CLASSIFIER
# ============================================================================

class DisclosureStatusClassifier:
    """
    Classifies each finding as:
    - MISSING: Not disclosed at all
    - INADEQUATE: Disclosed but insufficient detail
    - INCONSISTENT: Contradictory information
    - DISCLOSED: Present but needs justification
    """
    
    MISSING_INDICATORS = [
        'not disclosed', 'not mentioned', 'not provided', 'not specified',
        'absence of', 'missing', 'omitted'
    ]
    
    INADEQUATE_INDICATORS = [
        'insufficient', 'inadequate', 'vague', 'unclear', 'generic',
        'kindly elaborate', 'kindly provide details', 'kindly clarify'
    ]
    
    INCONSISTENT_INDICATORS = [
        'contradiction', 'inconsistent', 'mismatch', 'discrepancy',
        'reconcile', 'conflicting', 'differs from'
    ]
    
    def classify(self, query_text: str) -> str:
        """
        Classify disclosure status from query text
        
        Args:
            query_text: The observation/query text
            
        Returns:
            'MISSING' | 'INADEQUATE' | 'INCONSISTENT' | 'DISCLOSED'
        """
        text_lower = query_text.lower()
        
        # Check for inconsistencies first (highest priority)
        if any(ind in text_lower for ind in self.INCONSISTENT_INDICATORS):
            return 'INCONSISTENT'
        
        # Check for missing
        if any(ind in text_lower for ind in self.MISSING_INDICATORS):
            return 'MISSING'
        
        # Check for inadequate
        if any(ind in text_lower for ind in self.INADEQUATE_INDICATORS):
            return 'INADEQUATE'
        
        # Default: disclosed but needs attention
        return 'DISCLOSED'
    
    def get_tone_for_status(self, status: str) -> str:
        """
        Map disclosure status to appropriate NSE tone
        
        Returns:
            Tone descriptor for query formatting
        """
        tone_map = {
            'MISSING': 'DIRECTIVE',      # "LM is advised to disclose..."
            'INADEQUATE': 'STANDARD',    # "Kindly provide detailed..."
            'INCONSISTENT': 'CRITICAL',  # "Kindly reconcile the contradiction..."
            'DISCLOSED': 'SOFT'          # "Kindly clarify..."
        }
        
        return tone_map.get(status, 'STANDARD')


# ============================================================================
# 3️⃣ MATERIALITY SCORER
# ============================================================================

class MaterialityScorer:
    """
    Scores materiality based on company scale and issue impact
    
    This is CRITICAL for deciding:
    - Whether to force a Risk Factor
    - Whether to ask for ₹/% quantification
    - Severity level escalation
    """
    
    # Materiality thresholds (% of revenue)
    CRITICAL_THRESHOLD = 5.0   # >5% of revenue
    MATERIAL_THRESHOLD = 1.0   # >1% of revenue
    MINOR_THRESHOLD = 0.5      # >0.5% of revenue
    
    # Scale-based adjustments
    SMALL_COMPANY = 50    # ₹50 Cr
    MEDIUM_COMPANY = 500  # ₹500 Cr
    LARGE_COMPANY = 2000  # ₹2000 Cr
    
    def __init__(self):
        self.name = "Materiality Scorer"
    
    def score(self, query: Dict, company_profile: Dict) -> str:
        """
        Calculate materiality score for a query
        
        Args:
            query: Query dict with observation text
            company_profile: {revenue, employees, business_type}
            
        Returns:
            'CRITICAL' | 'MATERIAL' | 'MINOR' | 'HYGIENE'
        """
        revenue = company_profile.get('revenue', 0)
        
        if revenue == 0:
            # Can't calculate materiality without revenue
            return self._default_materiality(query)
        
        # Extract monetary values from query text
        observation = query.get('observation', '')
        amounts = self._extract_amounts(observation)
        
        if not amounts:
            return self._default_materiality(query)
        
        # Calculate materiality percentage
        max_amount = max(amounts)
        materiality_pct = (max_amount / revenue) * 100
        
        # Score based on thresholds
        if materiality_pct > self.CRITICAL_THRESHOLD:
            return 'CRITICAL'
        elif materiality_pct > self.MATERIAL_THRESHOLD:
            return 'MATERIAL'
        elif materiality_pct > self.MINOR_THRESHOLD:
            return 'MINOR'
        else:
            return 'HYGIENE'
    
    def _extract_amounts(self, text: str) -> List[float]:
        """Extract ₹ amounts from text"""
        amounts = []
        
        # Pattern: ₹X crores, ₹X lakhs, ₹X Cr, etc.
        crore_pattern = r'₹\s*(\d+(?:,\d+)?(?:\.\d+)?)\s*(?:crore|crores|Cr)'
        lakh_pattern = r'₹\s*(\d+(?:,\d+)?(?:\.\d+)?)\s*(?:lakh|lakhs|L)'
        
        # Find crores
        for match in re.finditer(crore_pattern, text, re.IGNORECASE):
            amount_str = match.group(1).replace(',', '')
            amounts.append(float(amount_str))
        
        # Find lakhs (convert to crores)
        for match in re.finditer(lakh_pattern, text, re.IGNORECASE):
            amount_str = match.group(1).replace(',', '')
            amounts.append(float(amount_str) / 100)  # lakhs to crores
        
        return amounts
    
    def _default_materiality(self, query: Dict) -> str:
        """
        Default materiality when can't calculate from amounts
        
        Uses severity and issue type as proxy
        """
        severity = query.get('severity', '')
        issue_id = query.get('issue_id', '')
        
        # Critical issues are material by default
        if 'Critical' in severity:
            return 'MATERIAL'
        
        # Financial/valuation issues are material
        if any(word in issue_id for word in ['REVENUE', 'FINANCIAL', 'VALUATION']):
            return 'MATERIAL'
        
        # Default to minor
        return 'MINOR'


# ============================================================================
# 4️⃣ QUERY COLLISION RESOLVER
# ============================================================================

class QueryCollisionResolver:
    """
    Merges duplicate or overlapping queries from System A and System B
    
    Example:
    - System A: "Litigation disclosure missing"
    - System B: "Litigation narrative inadequate"
    → Merge into ONE comprehensive query
    """
    
    # Topic groups for collision detection
    TOPIC_KEYWORDS = {
        'LITIGATION': ['litigation', 'legal', 'lawsuit', 'dispute', 'case'],
        'REVENUE': ['revenue', 'sales', 'turnover', 'income'],
        'CAPACITY': ['capacity', 'utilization', 'production'],
        'ATTRITION': ['attrition', 'employee', 'turnover', 'retention'],
        'SUPPLIER': ['supplier', 'vendor', 'procurement'],
        'CUSTOMER': ['customer', 'client', 'distributor'],
        'INSURANCE': ['insurance', 'coverage', 'policy'],
        'LEASE': ['lease', 'rental', 'property', 'premises'],
    }
    
    def resolve(self, queries: List[Dict]) -> List[Dict]:
        """
        Identify and merge colliding queries
        
        Args:
            queries: Combined list from System A + System B
            
        Returns:
            Deduplicated list with merged queries
        """
        if len(queries) <= 1:
            return queries
        
        # Group by topic
        topic_groups = self._group_by_topic(queries)
        
        # Merge within each group
        merged = []
        merged_count = 0
        
        for topic, group_queries in topic_groups.items():
            if len(group_queries) == 1:
                merged.append(group_queries[0])
            else:
                # Multiple queries on same topic - merge them
                merged_query = self._merge_queries(group_queries, topic)
                merged.append(merged_query)
                merged_count += len(group_queries) - 1
        
        if merged_count > 0:
            print(f"   [Resolver] Merged {merged_count} duplicate queries")
        
        return merged
    
    def _group_by_topic(self, queries: List[Dict]) -> Dict[str, List[Dict]]:
        """Group queries by topic"""
        groups = {}
        
        for query in queries:
            observation = query.get('observation', '').lower()
            
            # Find matching topic
            matched_topic = None
            for topic, keywords in self.TOPIC_KEYWORDS.items():
                if any(kw in observation for kw in keywords):
                    matched_topic = topic
                    break
            
            # Use issue_id as fallback
            if not matched_topic:
                matched_topic = query.get('issue_id', 'OTHER')
            
            if matched_topic not in groups:
                groups[matched_topic] = []
            
            groups[matched_topic].append(query)
        
        return groups
    
    def _merge_queries(self, queries: List[Dict], topic: str) -> Dict:
        """
        Merge multiple queries on same topic into one comprehensive query
        """
        # Use the most severe query as base
        base_query = max(queries, key=lambda q: self._severity_rank(q.get('severity', '')))
        
        # Combine observations
        observations = [q.get('observation', '') for q in queries]
        merged_observation = self._combine_observations(observations, topic)
        
        # Update base query
        base_query['observation'] = merged_observation
        base_query['merged_from'] = len(queries)
        
        return base_query
    
    def _severity_rank(self, severity: str) -> int:
        """Rank severity for selecting base query"""
        ranks = {
            'Critical - Valuation': 5,
            'Critical - Legal': 5,
            'Critical - Operational': 5,
            'Major': 4,
            'Material': 3,
            'Minor': 2,
            'Observation': 1,
            'Hygiene': 1
        }
        return ranks.get(severity, 0)
    
    def _combine_observations(self, observations: List[str], topic: str) -> str:
        """Combine multiple observations into one coherent query"""
        # For now, use the longest observation (most comprehensive)
        # TODO: In production, use LLM to synthesize
        return max(observations, key=len)


# ============================================================================
# 5️⃣ SEVERITY & TONE CONTROLLER
# ============================================================================

class SeverityToneController:
    """
    Maps issues to appropriate NSE severity levels and tone
    
    Ensures consistency across all queries
    """
    
    SEVERITY_LEVELS = [
        'Critical - Valuation',
        'Critical - Legal',
        'Critical - Operational',
        'Major',
        'Material',
        'Minor',
        'Observation',
        'Hygiene'
    ]
    
    # Tone templates
    TONES = {
        'DIRECTIVE': 'LM is advised to',
        'CRITICAL': 'Kindly reconcile',
        'STANDARD': 'Kindly provide',
        'SOFT': 'Kindly clarify'
    }
    
    def control(
        self, 
        query: Dict, 
        materiality: str, 
        disclosure_status: str
    ) -> Tuple[str, str]:
        """
        Determine appropriate severity and tone
        
        Args:
            query: Query dict
            materiality: 'CRITICAL' | 'MATERIAL' | 'MINOR' | 'HYGIENE'
            disclosure_status: 'MISSING' | 'INADEQUATE' | 'INCONSISTENT' | 'DISCLOSED'
            
        Returns:
            (severity, tone) tuple
        """
        
        # Start with current severity
        current_severity = query.get('severity', 'Material')
        
        # Escalate based on materiality
        if materiality == 'CRITICAL':
            if 'REVENUE' in query.get('issue_id', ''):
                severity = 'Critical - Valuation'
            elif 'LEGAL' in query.get('category', ''):
                severity = 'Critical - Legal'
            else:
                severity = 'Critical - Operational'
        elif materiality == 'MATERIAL':
            severity = 'Major'
        elif materiality == 'MINOR':
            severity = 'Material'
        else:
            severity = 'Observation'
        
        # Adjust tone based on disclosure status
        if disclosure_status == 'MISSING':
            tone = 'DIRECTIVE'
        elif disclosure_status == 'INCONSISTENT':
            tone = 'CRITICAL'
        elif disclosure_status == 'INADEQUATE':
            tone = 'STANDARD'
        else:
            tone = 'SOFT'
        
        return severity, tone


# ============================================================================
# 6️⃣ SECTION PLACEMENT ENFORCER
# ============================================================================

class SectionPlacementEnforcer:
    """
    Determines which DRHP section should contain the disclosure
    
    NSE often says: "Kindly ensure appropriate placement in [X] chapter"
    """
    
    SECTION_MAPPING = {
        # Revenue/Financial
        'REVENUE': 'Financial Information',
        'FINANCIAL': 'Financial Information',
        'VALUATION': 'Financial Information',
        
        # Risk
        'RISK': 'Risk Factors',
        'DEPENDENCY': 'Risk Factors',
        'VOLATILITY': 'Risk Factors',
        
        # Operations
        'CAPACITY': 'Business Overview',
        'MANUFACTURING': 'Business Overview',
        'OPERATIONS': 'Business Overview',
        'CUSTOMER': 'Business Overview',
        'SUPPLIER': 'Business Overview',
        
        # Legal
        'LITIGATION': 'Outstanding Litigation and Material Developments',
        'REGULATORY': 'Government and Other Approvals',
        'COMPLIANCE': 'Government and Other Approvals',
        
        # HR
        'ATTRITION': 'Business Overview',
        'EMPLOYEE': 'Business Overview',
        'MANAGEMENT': 'Our Management',
        
        # Contracts
        'LEASE': 'Material Contracts and Documents',
        'AGREEMENT': 'Material Contracts and Documents',
    }
    
    def enforce(self, query: Dict) -> str:
        """
        Determine appropriate section for disclosure
        
        Args:
            query: Query dict with issue_id and category
            
        Returns:
            Section name (DRHP chapter)
        """
        issue_id = query.get('issue_id', '')
        category = query.get('category', '')
        
        # Check issue_id keywords
        for keyword, section in self.SECTION_MAPPING.items():
            if keyword in issue_id.upper():
                return section
        
        # Check category
        for keyword, section in self.SECTION_MAPPING.items():
            if keyword in category.upper():
                return section
        
        # Default
        return 'Business Overview'


# ============================================================================
# MAIN NORMALIZATION LAYER
# ============================================================================

class InterpretationNormalizationLayer:
    """
    The complete interpretation and normalization pipeline
    
    Transforms raw findings from System A and System B into
    context-aware, properly calibrated NSE-style queries.
    """
    
    def __init__(self):
        """Initialize all normalizers"""
        self.business_normalizer = BusinessModelNormalizer()
        self.disclosure_classifier = DisclosureStatusClassifier()
        self.materiality_scorer = MaterialityScorer()
        self.collision_resolver = QueryCollisionResolver()
        self.severity_controller = SeverityToneController()
        self.section_enforcer = SectionPlacementEnforcer()
        
        print("✅ Interpretation & Normalization Layer initialized")
        print("   ✓ Business Model Normalizer")
        print("   ✓ Disclosure Status Classifier")
        print("   ✓ Materiality Scorer")
        print("   ✓ Query Collision Resolver")
        print("   ✓ Severity & Tone Controller")
        print("   ✓ Section Placement Enforcer")
    
    def normalize(
        self,
        queries: List[Dict[str, Any]],
        company_profile: Dict[str, Any],
        drhp_text: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Main normalization pipeline
        
        Args:
            queries: Raw queries from System A + System B
            company_profile: {revenue, employees, business_type}
            drhp_text: Full DRHP text (optional, for context)
            
        Returns:
            Normalized, calibrated queries ready for output
        """
        
        if not queries:
            return []
        
        print(f"\n{'='*80}")
        print(f"🧠 INTERPRETATION & NORMALIZATION LAYER")
        print(f"{'='*80}")
        print(f"Input: {len(queries)} raw queries")
        print(f"Company Profile: {company_profile.get('business_type', 'Unknown')}, "
              f"₹{company_profile.get('revenue', 0)} Cr")
        
        # Step 1: Business Model Normalization
        print(f"\n[Step 1/6] Business Model Normalization...")
        queries = self.business_normalizer.normalize(queries, company_profile)
        print(f"   After filtering: {len(queries)} queries")
        
        # Step 2: Classify Disclosure Status
        print(f"\n[Step 2/6] Disclosure Status Classification...")
        for query in queries:
            observation = query.get('observation', query.get('text', ''))
            status = self.disclosure_classifier.classify(observation)
            query['disclosure_status'] = status
        
        status_counts = {}
        for q in queries:
            status = q.get('disclosure_status', 'UNKNOWN')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        for status, count in status_counts.items():
            print(f"   {status}: {count}")
        
        # Step 3: Materiality Scoring
        print(f"\n[Step 3/6] Materiality Scoring...")
        for query in queries:
            materiality = self.materiality_scorer.score(query, company_profile)
            query['materiality'] = materiality
        
        materiality_counts = {}
        for q in queries:
            mat = q.get('materiality', 'UNKNOWN')
            materiality_counts[mat] = materiality_counts.get(mat, 0) + 1
        
        for mat, count in materiality_counts.items():
            print(f"   {mat}: {count}")
        
        # Step 4: Query Collision Resolution
        print(f"\n[Step 4/6] Query Collision Resolution...")
        queries = self.collision_resolver.resolve(queries)
        print(f"   After merging: {len(queries)} queries")
        
        # Step 5: Severity & Tone Control
        print(f"\n[Step 5/6] Severity & Tone Control...")
        for query in queries:
            materiality = query.get('materiality', 'MINOR')
            disclosure_status = query.get('disclosure_status', 'DISCLOSED')
            
            severity, tone = self.severity_controller.control(
                query, materiality, disclosure_status
            )
            
            query['severity'] = severity
            query['tone'] = tone
        
        # Step 6: Section Placement
        print(f"\n[Step 6/6] Section Placement Enforcement...")
        for query in queries:
            section = self.section_enforcer.enforce(query)
            query['recommended_section'] = section
        
        print(f"\n✅ Normalization complete: {len(queries)} calibrated queries")
        print(f"{'='*80}\n")
        
        return queries


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def get_interpretation_layer():
    """Factory function to get normalization layer instance"""
    return InterpretationNormalizationLayer()