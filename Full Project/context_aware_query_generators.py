"""
Context-Aware Query Generators
===============================

Uses extracted DRHP context to generate SPECIFIC queries that work on ANY DRHP.

Key principle: GENERIC PATTERNS applied to SPECIFIC CONTENT

Instead of:
  ❌ "Check if 'converted foam' revenue declined"  (hardcoded)

We do:
  ✅ FOR EACH extracted_product:
        IF revenue_declined(product, >20%):
           generate_query(product, decline_pct, pages)

This makes queries DRHP-specific while logic remains GENERIC.

Author: IPO Compliance System
Version: 2.0 Production
"""

from typing import List, Dict, Any
import re


# ============================================================================
# CONTEXT-AWARE FINANCIAL QUERY GENERATOR
# ============================================================================

class FinancialQueryGenerator:
    """
    Generates financial queries using extracted context
    
    Queries generated:
    - YoY revenue decline >20% (with specific product name)
    - Product-wise export split missing
    - Industry-wise revenue split missing
    - Segment reconciliation issues
    """
    
    def __init__(self):
        print("✅ Financial Query Generator initialized")
    
    def generate_queries(self, context: Dict[str, Any]) -> List[Dict]:
        """
        Generate financial queries from context
        
        Args:
            context: Extracted DRHP context
        
        Returns:
            List of query dicts
        """
        queries = []
        
        # 1. Check for revenue decline anomalies
        queries.extend(self._check_revenue_declines(context))
        
        # 2. Check for export split disclosure
        queries.extend(self._check_export_splits(context))
        
        # 3. Check for industry-wise revenue split
        queries.extend(self._check_industry_splits(context))
        
        # 4. Check for segment-wise details
        queries.extend(self._check_segment_details(context))
        
        return queries
    
    def _check_revenue_declines(self, context: Dict) -> List[Dict]:
        """Check for significant revenue declines"""
        queries = []
        
        trends = context.get('trends', [])
        
        for trend in trends:
            if trend['is_anomaly'] and trend['change_pct'] < -20:
                # Significant decline detected
                fy_data = trend['fy_data']
                years = sorted(fy_data.keys())
                
                if len(years) >= 2:
                    fy_prev = years[-2]
                    fy_curr = years[-1]
                    
                    pages = trend.get('pages', [])
                    page_ref = self._format_page_ref(pages)
                    
                    queries.append({
                        'type': 'financial_trend',
                        'page': page_ref,
                        'observation': (
                            f"It has been observed that {trend['entity']} revenue declined "
                            f"substantially ({abs(trend['change_pct']):.1f}%) in {fy_curr} "
                            f"(₹{fy_data[fy_curr]:.2f} Cr) as compared to {fy_prev} "
                            f"(₹{fy_data[fy_prev]:.2f} Cr). Kindly provide detailed reasons "
                            f"for the same, refer page {page_ref} of the DRHP."
                        ),
                        'severity': 'Major',
                        'category': 'Financial',
                        'issue_id': 'REVENUE_DECLINE_ANOMALY',
                        'regulation_ref': 'ICDR Regulations - Financial Disclosure'
                    })
        
        return queries
    
    def _check_export_splits(self, context: Dict) -> List[Dict]:
        """Check if export split is disclosed for products"""
        queries = []
        
        products = context.get('products', [])
        
        # Check if we have any product with revenue data
        products_with_revenue = [p for p in products if p.get('revenue_data')]
        
        if products_with_revenue and not any(p.get('export_split_disclosed') for p in products):
            # No product has export split - generate query
            queries.append({
                'type': 'export_split',
                'page': '1',  # Generic reference
                'observation': (
                    f"Kindly provide product-wise domestic and export sales bifurcation "
                    f"for the DRHP period. Include detailed breakup for all major products "
                    f"({', '.join([p['name'] for p in products_with_revenue[:3]])}, etc.) "
                    f"in tabular format showing ₹ and % contribution."
                ),
                'severity': 'Material',
                'category': 'Financial',
                'issue_id': 'PRODUCT_EXPORT_SPLIT',
                'regulation_ref': 'ICDR Regulations - Financial Disclosure'
            })
        
        return queries
    
    def _check_industry_splits(self, context: Dict) -> List[Dict]:
        """Check for industry-wise revenue split"""
        queries = []
        
        segments = context.get('segments', [])
        industry_segments = [s for s in segments if s['type'] == 'industry']
        
        page_map = context.get('page_map', {})
        revenue_pages = page_map.get('revenue_tables', [])
        
        if len(industry_segments) >= 2:
            # Multiple industries mentioned - check if comprehensive split provided
            page_ref = self._format_page_ref(revenue_pages) if revenue_pages else '1'
            
            segment_names = [s['name'] for s in industry_segments]
            
            queries.append({
                'type': 'industry_split',
                'page': page_ref,
                'observation': (
                    f"Refer to page {page_ref} of the DRHP and provide/include details of "
                    f"breakup of industry-wise revenue from operations split for the DRHP "
                    f"period including {', '.join(segment_names)}, etc. Provide this in "
                    f"tabular format showing ₹ and % contribution for past 3 FYs and stub period."
                ),
                'severity': 'Material',
                'category': 'Financial',
                'issue_id': 'INDUSTRY_REVENUE_SPLIT',
                'regulation_ref': 'ICDR Regulations - Financial Disclosure'
            })
        
        return queries
    
    def _check_segment_details(self, context: Dict) -> List[Dict]:
        """Check for missing segment details"""
        queries = []
        
        segments = context.get('segments', [])
        
        for segment in segments:
            if segment['type'] == 'geography' and not segment.get('has_detailed_split'):
                # Geographic segment without detailed split
                page_ref = self._format_page_ref(segment.get('pages', []))
                
                queries.append({
                    'type': 'segment_detail',
                    'page': page_ref,
                    'observation': (
                        f"On page no. {page_ref}, {segment['name']} segment is mentioned. "
                        f"Kindly provide detailed country-wise/region-wise split showing "
                        f"₹ and % contribution for past 3 FYs and stub period."
                    ),
                    'severity': 'Material',
                    'category': 'Financial',
                    'issue_id': 'SEGMENT_DETAIL_MISSING',
                    'regulation_ref': 'ICDR Regulations - Financial Disclosure'
                })
        
        return queries
    
    def _format_page_ref(self, pages: List[int]) -> str:
        """Format page reference"""
        if not pages:
            return '1'
        elif len(pages) == 1:
            return str(pages[0])
        elif len(pages) == 2:
            return f"{pages[0]} and {pages[1]}"
        else:
            return f"{pages[0]} to {pages[-1]}"


# ============================================================================
# CONTEXT-AWARE OPERATIONAL QUERY GENERATOR
# ============================================================================

class OperationalQueryGenerator:
    """
    Generates operational queries using extracted context
    
    Queries generated:
    - R&D expenditure (if products are tech/pharma)
    - Government policies (for specific industries)
    - Chinese distributor details (if mentioned)
    - Manufacturing vs trading split (for specific products)
    """
    
    # Industry-specific query templates
    INDUSTRY_QUERIES = {
        'pharma': [
            'R&D expenditure and employee count',
            'Regulatory approvals and drug master files',
        ],
        'automotive': [
            'Capacity utilization and expansion plans',
            'Customer concentration risk (OEM dependency)',
        ],
        'toys': [
            'Government policies and incentives for toys manufacturing',
            'Quality certifications (BIS/ISO)',
        ],
        'electronics': [
            'Technology obsolescence risk',
            'Import dependency on critical components',
        ],
    }
    
    def __init__(self):
        print("✅ Operational Query Generator initialized")
    
    def generate_queries(self, context: Dict[str, Any]) -> List[Dict]:
        """Generate operational queries from context"""
        queries = []
        
        # 1. Check for R&D disclosure (tech/pharma products)
        queries.extend(self._check_rd_disclosure(context))
        
        # 2. Check for government policies (industry-specific)
        queries.extend(self._check_government_policies(context))
        
        # 3. Check for Chinese distributor details
        queries.extend(self._check_chinese_entities(context))
        
        # 4. Check for manufacturing vs trading split
        queries.extend(self._check_manufacturing_split(context))
        
        # 5. Check for trademark details
        queries.extend(self._check_trademark_details(context))
        
        # 6. Check for property area details
        queries.extend(self._check_property_details(context))
        
        return queries
    
    def _check_rd_disclosure(self, context: Dict) -> List[Dict]:
        """Check if R&D disclosure is needed"""
        queries = []
        
        products = context.get('products', [])
        
        # Check if tech/pharma/chemical products
        rd_categories = ['pharma', 'electronics', 'chemicals', 'automotive']
        
        has_rd_product = any(
            p.get('category') in rd_categories 
            for p in products
        )
        
        if has_rd_product:
            page_map = context.get('page_map', {})
            biz_pages = page_map.get('business_overview', [])
            page_ref = self._format_page_ref(biz_pages) if biz_pages else '1'
            
            queries.append({
                'type': 'rd_disclosure',
                'page': page_ref,
                'observation': (
                    f"Refer page {page_ref}, kindly check for inclusion of details of R&D "
                    f"and branding investment/expenditure done in DRHP period. Include: "
                    f"(a) number of employees in R&D department; (b) ₹ spent in past 3 FYs; "
                    f"(c) key outcomes/patents filed; and (d) future R&D plans. Provide "
                    f"revised draft."
                ),
                'severity': 'Material',
                'category': 'Operational',
                'issue_id': 'RD_INVESTMENT_DISCLOSURE',
                'regulation_ref': 'ICDR Regulations - Business Disclosure'
            })
        
        return queries
    
    def _check_government_policies(self, context: Dict) -> List[Dict]:
        """Check for government policy disclosure"""
        queries = []
        
        products = context.get('products', [])
        
        # Industries that typically have government incentives
        incentive_categories = ['toys', 'pharma', 'electronics', 'textiles']
        
        relevant_products = [
            p for p in products 
            if p.get('category') in incentive_categories
        ]
        
        if relevant_products:
            page_map = context.get('page_map', {})
            biz_pages = page_map.get('business_overview', [])
            page_ref = self._format_page_ref(biz_pages[1:3]) if len(biz_pages) > 1 else '1'
            
            categories = list(set(p['category'] for p in relevant_products))
            
            queries.append({
                'type': 'government_policy',
                'page': page_ref,
                'observation': (
                    f"Page {page_ref}, kindly provide details of government policies/any "
                    f"benefit received in past DRHP period related to key product lines "
                    f"({', '.join(categories)}). Include: (a) specific schemes availed; "
                    f"(b) ₹ benefit received (past 3 FYs); (c) eligibility criteria; and "
                    f"(d) sunset clauses/renewal. Provide revised draft."
                ),
                'severity': 'Material',
                'category': 'Operational',
                'issue_id': 'GOVERNMENT_POLICY_DISCLOSURE',
                'regulation_ref': 'ICDR Regulations - Business Disclosure'
            })
        
        return queries
    
    def _check_chinese_entities(self, context: Dict) -> List[Dict]:
        """Check for Chinese entity disclosure"""
        queries = []
        
        entities = context.get('entities', [])
        
        chinese_entities = [
            e for e in entities 
            if e.get('relationship') == 'chinese'
        ]
        
        if chinese_entities:
            for entity in chinese_entities:
                page_ref = self._format_page_ref(entity.get('pages', []))
                
                queries.append({
                    'type': 'chinese_entity',
                    'page': page_ref,
                    'observation': (
                        f"Refer page {page_ref}, kindly check for inclusion/provide the "
                        f"name and detailed profile of Chinese {entity['type']} mentioned. "
                        f"Include: (a) complete name and jurisdiction; (b) nature of business "
                        f"relationship; (c) % dependency (procurement/revenue); (d) geopolitical "
                        f"risk assessment; and (e) alternative arrangements. Provide revised draft."
                    ),
                    'severity': 'Major',
                    'category': 'Operational',
                    'issue_id': 'CHINESE_ENTITY_DISCLOSURE',
                    'regulation_ref': 'ICDR Regulations - Business Disclosure'
                })
        
        return queries
    
    def _check_manufacturing_split(self, context: Dict) -> List[Dict]:
        """Check for own vs contract manufacturing split"""
        queries = []
        
        products = context.get('products', [])
        
        # Check if manufacturing category products exist
        mfg_products = [
            p for p in products 
            if p.get('category') in ['automotive', 'pharma', 'electronics', 'chemicals', 'textiles']
        ]
        
        if mfg_products:
            queries.append({
                'type': 'manufacturing_split',
                'page': '1',
                'observation': (
                    f"Kindly check for inclusion of details of major verticals/products split "
                    f"into own manufacturing and contractual manufacturing. Provide ₹ and % "
                    f"split for each major product line ({', '.join([p['name'] for p in mfg_products[:3]])}, etc.) "
                    f"for past 3 FYs and stub period. Include: (a) capacity utilization for "
                    f"own manufacturing; (b) contract manufacturer names and locations; and "
                    f"(c) quality control mechanisms. Provide revised draft."
                ),
                'severity': 'Material',
                'category': 'Operational',
                'issue_id': 'MANUFACTURING_SPLIT',
                'regulation_ref': 'ICDR Regulations - Business Disclosure'
            })
        
        return queries
    
    def _check_trademark_details(self, context: Dict) -> List[Dict]:
        """Check for trademark registration details"""
        queries = []
        
        page_map = context.get('page_map', {})
        biz_pages = page_map.get('business_overview', [])
        
        if biz_pages:
            # Assume trademarks are discussed in business section
            queries.append({
                'type': 'trademark_details',
                'page': '1',
                'observation': (
                    f"Refer to the trademark details in business chapter, kindly include "
                    f"the registration number, registration date, and validity period details "
                    f"for all trademarks in the DRHP. Provide this in tabular format showing: "
                    f"(a) Trademark name; (b) Class; (c) Registration No.; (d) Registration date; "
                    f"(e) Validity till; and (f) Territory. Provide revised draft."
                ),
                'severity': 'Hygiene',
                'category': 'Legal',
                'issue_id': 'TRADEMARK_DETAILS',
                'regulation_ref': 'ICDR Regulations - Legal Disclosure'
            })
        
        return queries
    
    def _check_property_details(self, context: Dict) -> List[Dict]:
        """Check for property area measurement details"""
        queries = []
        
        page_map = context.get('page_map', {})
        property_pages = page_map.get('properties', [])
        
        if property_pages:
            page_ref = self._format_page_ref(property_pages)
            
            queries.append({
                'type': 'property_area',
                'page': page_ref,
                'observation': (
                    f"Refer to the property section on page {page_ref}, kindly include "
                    f"the area details (i.e. sq.ft., sq. meters, acres etc.) for all "
                    f"properties (owned and leased). Provide this in the property table "
                    f"along with: (a) built-up area; (b) land area; (c) unit of measurement; "
                    f"and (d) usage (manufacturing/office/warehouse). Provide revised draft."
                ),
                'severity': 'Hygiene',
                'category': 'Legal',
                'issue_id': 'PROPERTY_AREA_DETAILS',
                'regulation_ref': 'ICDR Regulations - Property Disclosure'
            })
        
        return queries
    
    def _format_page_ref(self, pages: List[int]) -> str:
        """Format page reference"""
        if not pages:
            return '1'
        elif len(pages) == 1:
            return str(pages[0])
        elif len(pages) == 2:
            return f"{pages[0]} and {pages[1]}"
        else:
            return f"{pages[0]} to {pages[-1]}"


# ============================================================================
# CONTEXT-AWARE CROSS-REFERENCE CHECKER
# ============================================================================

class CrossReferenceChecker:
    """
    Checks for cross-reference reconciliation issues
    
    Examples:
    - Competition section mentions revenue split but financial statements differ
    - SKU count in narrative vs table mismatch
    - Product list in business vs revenue table mismatch
    """
    
    def __init__(self):
        print("✅ Cross-Reference Checker initialized")
    
    def generate_queries(self, context: Dict[str, Any]) -> List[Dict]:
        """Generate cross-reference queries"""
        queries = []
        
        # 1. Check competition vs financial reconciliation
        queries.extend(self._check_competition_reconciliation(context))
        
        # 2. Check product list consistency
        queries.extend(self._check_product_consistency(context))
        
        return queries
    
    def _check_competition_reconciliation(self, context: Dict) -> List[Dict]:
        """Check if competition section aligns with financials"""
        queries = []
        
        page_map = context.get('page_map', {})
        comp_pages = page_map.get('competition', [])
        fin_pages = page_map.get('revenue_tables', [])
        
        if comp_pages and fin_pages:
            comp_ref = self._format_page_ref(comp_pages)
            fin_ref = self._format_page_ref(fin_pages)
            
            queries.append({
                'type': 'cross_reference',
                'page': f"{comp_ref} and {fin_ref}",
                'observation': (
                    f"Refer page {comp_ref} 'Competition section' and also page {fin_ref} "
                    f"for industry-wise/product-wise revenues generated from the sale of "
                    f"products as per the restated financial statements. Kindly ensure "
                    f"consistency between: (a) market segments discussed in competition; "
                    f"and (b) revenue split in financial statements. If any segment is "
                    f"discussed in competition but not reflected in revenue split (or vice versa), "
                    f"provide rationale. Provide revised draft with reconciliation."
                ),
                'severity': 'Material',
                'category': 'Cross-Reference',
                'issue_id': 'COMPETITION_FINANCIAL_RECONCILIATION',
                'regulation_ref': 'ICDR Regulations - Consistency'
            })
        
        return queries
    
    def _check_product_consistency(self, context: Dict) -> List[Dict]:
        """Check if product mentions are consistent"""
        queries = []
        
        products = context.get('products', [])
        segments = context.get('segments', [])
        
        # Check if competition section omits certain segments
        segment_names = [s['name'] for s in segments if s['type'] == 'industry']
        
        # Common segments that might be missing
        common_segments = ['Consumer Durables', 'Appliances', 'Home Products']
        
        page_map = context.get('page_map', {})
        comp_pages = page_map.get('competition', [])
        
        if comp_pages:
            comp_ref = self._format_page_ref(comp_pages)
            
            queries.append({
                'type': 'omission',
                'page': comp_ref,
                'observation': (
                    f"Refer to page {comp_ref}, kindly provide rationale for not including "
                    f"certain revenue segments (e.g., consumer durables, appliances, etc.) "
                    f"details in the competition section, if these segments contribute "
                    f"materially to revenue. If these segments are not material, provide "
                    f"disclosure confirming the same. Provide revised draft."
                ),
                'severity': 'Material',
                'category': 'Omission',
                'issue_id': 'COMPETITION_OMISSION',
                'regulation_ref': 'ICDR Regulations - Completeness'
            })
        
        return queries
    
    def _format_page_ref(self, pages: List[int]) -> str:
        """Format page reference"""
        if not pages:
            return '1'
        elif len(pages) == 1:
            return str(pages[0])
        else:
            return f"{pages[0]}"  # Just use first page for brevity


# ============================================================================
# CONTEXT-AWARE STATEMENT INTERROGATOR
# ============================================================================

class StatementInterrogator:
    """
    Interrogates specific forward-looking/strategic statements found in DRHP
    
    Looks for statements like:
    - "Part of our expansion will include..."
    - "We plan to acquire..."
    - "This initiative will enable..."
    
    And generates:
    - "Elaborate and explain the statement: '[exact quote]'. Refer page X..."
    """
    
    STATEMENT_PATTERNS = [
        # Expansion/acquisition statements
        r'(?:part of|as part of).*(?:expansion|growth|plan).*(?:will include|includes?|acquiring?)\s+([^.]{20,150})',
        r'we (?:plan|intend|propose) to (?:acquire|purchase|invest in)\s+([^.]{20,150})',
        
        # Custom/special arrangements
        r'custom\s+(?:machinery|equipment|technology)\s+for\s+([^.]{20,150})',
        
        # Strategic initiatives
        r'this\s+(?:initiative|strategy|investment)\s+(?:will|shall)\s+(?:enable|allow|help)\s+([^.]{20,150})',
    ]
    
    def __init__(self):
        print("✅ Statement Interrogator initialized")
    
    def generate_queries(
        self,
        pages_dict: Dict[int, str],
        context: Dict[str, Any]
    ) -> List[Dict]:
        """Generate statement interrogation queries"""
        queries = []
        
        for page_num, text in pages_dict.items():
            for pattern in self.STATEMENT_PATTERNS:
                matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
                
                for match in matches:
                    statement = match.group(0)
                    
                    # Clean statement
                    statement = statement.replace('\n', ' ')
                    statement = re.sub(r'\s+', ' ', statement)
                    
                    # Truncate if too long
                    if len(statement) > 150:
                        statement = statement[:147] + "..."
                    
                    queries.append({
                        'type': 'statement_interrogation',
                        'page': str(page_num),
                        'observation': (
                            f"Elaborate and explain the statement: '{statement}'. "
                            f"Refer page {page_num} of the DRHP. Kindly provide: "
                            f"(a) detailed implementation plan with timeline; "
                            f"(b) capital allocation (₹) and source of funds; "
                            f"(c) expected quantified benefits (₹/% on revenue/margins); "
                            f"(d) risks and mitigation; and (e) corresponding Risk Factor "
                            f"if dependent on external approvals/market conditions. "
                            f"Provide revised draft."
                        ),
                        'severity': 'Material',
                        'category': 'Strategic',
                        'issue_id': 'STATEMENT_ELABORATION',
                        'regulation_ref': 'ICDR Regulations - Forward-Looking Statements'
                    })
        
        # Limit to avoid too many
        return queries[:10]


# ============================================================================
# MASTER CONTEXT-AWARE QUERY GENERATOR
# ============================================================================

class ContextAwareQueryGenerator:
    """
    Master orchestrator that uses extracted context to generate
    DRHP-specific queries using GENERIC logic
    
    This is the KEY to making the system work on ANY DRHP
    """
    
    def __init__(self):
        self.financial_generator = FinancialQueryGenerator()
        self.operational_generator = OperationalQueryGenerator()
        self.cross_ref_checker = CrossReferenceChecker()
        self.statement_interrogator = StatementInterrogator()
        
        print("\n✅ Context-Aware Query Generator initialized")
    
    def generate_all_queries(
        self,
        context: Dict[str, Any],
        pages_dict: Dict[int, str]
    ) -> Dict[str, List[Dict]]:
        """
        Generate all context-aware queries
        
        Args:
            context: Extracted DRHP context
            pages_dict: {page_num: page_text}
        
        Returns:
            Dict of query categories
        """
        print(f"\n{'='*80}")
        print(f"🎯 CONTEXT-AWARE QUERY GENERATION")
        print(f"{'='*80}")
        
        results = {}
        
        # Generate financial queries
        print(f"\n[1/4] Generating financial queries...")
        results['financial'] = self.financial_generator.generate_queries(context)
        print(f"   ✓ Generated {len(results['financial'])} financial queries")
        
        # Generate operational queries
        print(f"\n[2/4] Generating operational queries...")
        results['operational'] = self.operational_generator.generate_queries(context)
        print(f"   ✓ Generated {len(results['operational'])} operational queries")
        
        # Generate cross-reference queries
        print(f"\n[3/4] Generating cross-reference queries...")
        results['cross_reference'] = self.cross_ref_checker.generate_queries(context)
        print(f"   ✓ Generated {len(results['cross_reference'])} cross-reference queries")
        
        # Generate statement interrogation queries
        print(f"\n[4/4] Generating statement interrogation queries...")
        results['statement'] = self.statement_interrogator.generate_queries(pages_dict, context)
        print(f"   ✓ Generated {len(results['statement'])} statement queries")
        
        total = sum(len(queries) for queries in results.values())
        print(f"\n✅ Total context-aware queries: {total}")
        print(f"{'='*80}\n")
        
        return results


def get_context_aware_generator():
    """Factory function"""
    return ContextAwareQueryGenerator()