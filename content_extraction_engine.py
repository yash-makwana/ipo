"""
Content-Aware Extraction Engine
================================

Dynamically extracts DRHP-specific content to make the compliance system
work on ANY DRHP, not just one specific document.

Extracts:
1. Products/SKUs (from tables and narrative)
2. Revenue segments (automotive, pharma, etc.)
3. Business verticals (manufacturing, trading, services)
4. Financial trends (YoY changes per product/segment)
5. Key entities (suppliers, customers, subsidiaries)
6. Page mappings (which pages discuss what topics)
7. Table structures (for cross-reference validation)

This enables GENERIC pattern detection on SPECIFIC content.

Author: IPO Compliance System
Version: 2.0 Production
"""

import re
from typing import List, Dict, Any, Set, Tuple, Optional
from collections import defaultdict
from dataclasses import dataclass
import json


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class Product:
    """Represents a product/SKU extracted from DRHP"""
    name: str
    category: str
    mentioned_pages: List[int]
    revenue_data: Dict[str, float]  # {fiscal_year: revenue}
    export_split_disclosed: bool
    sku_count: Optional[int] = None


@dataclass
class RevenueSegment:
    """Represents a revenue/business segment"""
    name: str
    type: str  # 'industry', 'geography', 'product'
    pages: List[int]
    revenue_data: Dict[str, float]
    has_detailed_split: bool


@dataclass
class FinancialTrend:
    """Represents a detected financial trend/anomaly"""
    metric: str  # 'revenue', 'margin', 'volume'
    entity: str  # product/segment name
    fy_data: Dict[str, float]
    change_pct: float
    is_anomaly: bool  # >20% change
    pages: List[int]


@dataclass
class Entity:
    """Represents a business entity (supplier/customer/subsidiary)"""
    name: str
    type: str  # 'supplier', 'customer', 'subsidiary', 'distributor'
    relationship: str  # 'exclusive', 'key', 'related_party'
    pages: List[int]
    financial_dependency: Optional[float] = None  # % of procurement/revenue


# ============================================================================
# PRODUCT EXTRACTOR
# ============================================================================

class ProductExtractor:
    """
    Extracts all products/SKUs from DRHP
    
    Sources:
    - Revenue tables (product-wise breakup)
    - Business overview narrative
    - Product descriptions
    """
    
    # Product table patterns
    PRODUCT_TABLE_PATTERNS = [
        r'product[\s-]*wise.*revenue',
        r'revenue.*product[\s-]*wise',
        r'break[\s-]*up.*product',
        r'product.*split',
    ]
    
    # Common product/category indicators
    CATEGORY_KEYWORDS = {
        'automotive': r'automotive|vehicle|automobile|car|truck',
        'pharma': r'pharmaceutical|pharma|drug|medicine|api|formulation',
        'fmcg': r'consumer\s+goods|fmcg|packaged\s+food',
        'textiles': r'textile|fabric|garment|apparel',
        'chemicals': r'chemical|polymer|resin',
        'electronics': r'electronic|semiconductor|circuit',
        'toys': r'toys|plaything',
        'foam': r'foam|cushion|padding',
        'appliances': r'appliance|durables|white\s+goods',
    }
    
    def __init__(self):
        self.products = []
        print("✅ Product Extractor initialized")
    
    def extract_products(self, pages_dict: Dict[int, str]) -> List[Product]:
        """
        Extract all products from DRHP
        
        Args:
            pages_dict: {page_num: page_text}
        
        Returns:
            List of Product objects
        """
        print("\n📦 Extracting products from DRHP...")
        
        # Find product tables
        product_tables = self._find_product_tables(pages_dict)
        
        # Extract products from tables
        table_products = self._extract_from_tables(product_tables, pages_dict)
        
        # Extract products from narrative
        narrative_products = self._extract_from_narrative(pages_dict)
        
        # Merge and deduplicate
        all_products = self._merge_products(table_products, narrative_products)
        
        # If still no products, try fallback
        if not all_products:
            all_products = self._fallback_extraction(pages_dict)
        
        print(f"   ✓ Extracted {len(all_products)} unique products")
        
        self.products = all_products
        return all_products
    
    def _find_product_tables(self, pages_dict: Dict[int, str]) -> Dict[int, str]:
        """Find pages containing product-wise revenue tables"""
        tables = {}
        
        for page_num, text in pages_dict.items():
            text_lower = text.lower()
            
            # Check for product table indicators
            for pattern in self.PRODUCT_TABLE_PATTERNS:
                if re.search(pattern, text_lower):
                    tables[page_num] = text
                    break
        
        return tables
    
    def _extract_from_tables(
        self, 
        table_pages: Dict[int, str],
        all_pages: Dict[int, str]
    ) -> List[Product]:
        """Extract products from revenue tables"""
        products = []
        
        for page_num, text in table_pages.items():
            # Look for product names followed by revenue figures
            # Pattern: Product Name | ₹XX.XX | ₹YY.YY | ₹ZZ.ZZ
            
            # Find lines with product names and numbers
            lines = text.split('\n')
            
            for line in lines:
                # Skip headers and totals
                if any(word in line.lower() for word in ['total', 'particulars', 'product', 'year']):
                    continue
                
                # Look for product name followed by numbers
                # Pattern: "ProductName ₹XXX ₹YYY" or "ProductName XXX YYY"
                if re.search(r'\d+(?:,\d+)*(?:\.\d+)?', line):
                    # Extract product name (first word/phrase)
                    product_name = self._extract_product_name(line)
                    
                    if product_name and len(product_name) > 2:
                        # Extract revenue figures
                        revenue_data = self._extract_revenue_figures(line)
                        
                        # Categorize product
                        category = self._categorize_product(product_name)
                        
                        products.append(Product(
                            name=product_name,
                            category=category,
                            mentioned_pages=[page_num],
                            revenue_data=revenue_data,
                            export_split_disclosed=False  # Will check later
                        ))
        
        return products
    
    def _extract_product_name(self, line: str) -> str:
        """Extract product name from table line"""
        # Remove common prefixes
        line = re.sub(r'^\d+[\.\)]\s*', '', line)  # Remove numbering
        
        # Take text before first number or special char
        match = re.search(r'^([A-Za-z\s&\-]+?)(?:\s+₹|\s+\d|$)', line)
        
        if match:
            name = match.group(1).strip()
            # Clean up
            name = re.sub(r'\s+', ' ', name)
            return name
        
        return ""
    
    def _extract_revenue_figures(self, line: str) -> Dict[str, float]:
        """Extract revenue figures from line (assumes FY order)"""
        revenue_data = {}
        
        # Find all numbers (crores assumed)
        numbers = re.findall(r'(\d+(?:,\d+)?(?:\.\d+)?)', line)
        
        # Map to fiscal years (assume last 3 years + stub)
        fy_labels = ['FY22', 'FY23', 'FY24', 'FY25']
        
        for i, num_str in enumerate(numbers[:4]):  # Take first 4 numbers
            try:
                value = float(num_str.replace(',', ''))
                if i < len(fy_labels):
                    revenue_data[fy_labels[i]] = value
            except ValueError:
                continue
        
        return revenue_data
    
    def _categorize_product(self, product_name: str) -> str:
        """Categorize product based on name"""
        name_lower = product_name.lower()
        
        for category, pattern in self.CATEGORY_KEYWORDS.items():
            if re.search(pattern, name_lower):
                return category
        
        return 'other'
    
    def _extract_from_narrative(self, pages_dict: Dict[int, str]) -> List[Product]:
        """Extract products mentioned in business overview narrative"""
        products = []
        
        # Look for "our products include", "we manufacture", etc.
        trigger_patterns = [
            r'(?:our\s+)?products?\s+include[s]?\s*:?\s*(.+?)(?:\.|;|and)',
            r'we\s+(?:manufacture|produce|offer)\s+(.+?)(?:\.|;|including)',
            r'product\s+portfolio\s+(?:comprises|includes)\s*:?\s*(.+?)(?:\.|;)',
        ]
        
        for page_num, text in pages_dict.items():
            for pattern in trigger_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
                
                for match in matches:
                    product_list = match.group(1)
                    
                    # Split by commas/and
                    items = re.split(r',|\s+and\s+', product_list)
                    
                    for item in items:
                        item = item.strip()
                        if len(item) > 3 and len(item) < 50:
                            category = self._categorize_product(item)
                            
                            products.append(Product(
                                name=item,
                                category=category,
                                mentioned_pages=[page_num],
                                revenue_data={},
                                export_split_disclosed=False
                            ))
        
        return products
    
    def _merge_products(
        self,
        table_products: List[Product],
        narrative_products: List[Product]
    ) -> List[Product]:
        """Merge and deduplicate products from different sources"""
        merged = {}
        
        # Add table products (priority)
        for product in table_products:
            key = product.name.lower().strip()
            merged[key] = product
        
        # Add narrative products (if not duplicate)
        for product in narrative_products:
            key = product.name.lower().strip()
            
            if key not in merged:
                # Check for partial matches
                is_duplicate = False
                for existing_key in merged.keys():
                    if key in existing_key or existing_key in key:
                        # Merge pages
                        merged[existing_key].mentioned_pages.extend(product.mentioned_pages)
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    merged[key] = product
                    
        # Fallback: If no products found, scan for category keywords
        if not merged:
            print("   ⚠️ No products found via standard extraction. Using fallback keyword scan...")
            full_text = " ".join([p.name for p in table_products] + [p.name for p in narrative_products]) # This is empty but logical placeholder
            # Actually need access to page text here, but method signature limits us.
            # We will rely on extract_products caller or simply return empty list and let caller handle?
            # Better: The caller (extract_products) has pages_dict. Let's move fallback there or hack it here?
            # We can't access pages_dict here easily without changing signature.
            # Let's change extract_products instead.
            pass
        
        return list(merged.values())
        
    def _fallback_extraction(self, pages_dict: Dict[int, str]) -> List[Product]:
        """Scan for category keywords if standard extraction fails"""
        found_products = []
        full_text = " ".join(pages_dict.values()).lower()
        
        for category, pattern in self.CATEGORY_KEYWORDS.items():
            if re.search(pattern, full_text):
                print(f"   ✓ Fallback: Detected '{category}' product context")
                found_products.append(Product(
                    name=f"{category.title()} Products",
                    category=category,
                    mentioned_pages=[1], # Dummy page
                    revenue_data={},
                    export_split_disclosed=False
                ))
        return found_products


# ============================================================================
# FINANCIAL TREND ANALYZER
# ============================================================================

class FinancialTrendAnalyzer:
    """
    Analyzes financial trends and detects anomalies
    
    Detects:
    - YoY revenue changes >20%
    - Margin compression/expansion
    - Product-wise trend reversals
    """
    
    ANOMALY_THRESHOLD = 20.0  # 20% change is anomalous
    
    def __init__(self):
        print("✅ Financial Trend Analyzer initialized")
    
    def analyze_trends(
        self,
        products: List[Product],
        pages_dict: Dict[int, str]
    ) -> List[FinancialTrend]:
        """
        Analyze financial trends for all products
        
        Returns:
            List of detected trends/anomalies
        """
        print("\n📈 Analyzing financial trends...")
        
        trends = []
        
        for product in products:
            if len(product.revenue_data) >= 2:
                # Analyze YoY changes
                product_trends = self._analyze_product_trends(product)
                trends.extend(product_trends)
        
        # Sort by anomaly severity
        trends.sort(key=lambda t: abs(t.change_pct), reverse=True)
        
        print(f"   ✓ Detected {len(trends)} financial trends")
        anomalies = [t for t in trends if t.is_anomaly]
        print(f"   ✓ {len(anomalies)} anomalies (>20% change)")
        
        return trends
    
    def _analyze_product_trends(self, product: Product) -> List[FinancialTrend]:
        """Analyze trends for a single product"""
        trends = []
        
        # Get sorted fiscal years
        sorted_years = sorted(product.revenue_data.keys())
        
        # Calculate YoY changes
        for i in range(len(sorted_years) - 1):
            fy_prev = sorted_years[i]
            fy_curr = sorted_years[i + 1]
            
            rev_prev = product.revenue_data[fy_prev]
            rev_curr = product.revenue_data[fy_curr]
            
            # Calculate change %
            if rev_prev > 0:
                change_pct = ((rev_curr - rev_prev) / rev_prev) * 100
            else:
                change_pct = 100.0 if rev_curr > 0 else 0.0
            
            # Check if anomaly
            is_anomaly = abs(change_pct) >= self.ANOMALY_THRESHOLD
            
            trends.append(FinancialTrend(
                metric='revenue',
                entity=product.name,
                fy_data={fy_prev: rev_prev, fy_curr: rev_curr},
                change_pct=change_pct,
                is_anomaly=is_anomaly,
                pages=product.mentioned_pages
            ))
        
        return trends


# ============================================================================
# SEGMENT EXTRACTOR
# ============================================================================

class SegmentExtractor:
    """
    Extracts revenue/business segments
    
    Types:
    - Industry segments (automotive, pharma, etc.)
    - Geographic segments (domestic, export, country-wise)
    - Product segments (product lines)
    """
    
    SEGMENT_PATTERNS = {
        'industry': [
            r'industry[\s-]*wise.*revenue',
            r'segment[\s-]*wise.*revenue',
            r'sector[\s-]*wise',
        ],
        'geography': [
            r'(?:domestic|export).*revenue',
            r'geographic.*split',
            r'country[\s-]*wise',
            r'region[\s-]*wise',
        ],
        'product': [
            r'product[\s-]*line',
            r'business[\s-]*vertical',
        ]
    }
    
    def __init__(self):
        print("✅ Segment Extractor initialized")
    
    def extract_segments(self, pages_dict: Dict[int, str]) -> List[RevenueSegment]:
        """Extract all revenue segments"""
        print("\n🎯 Extracting revenue segments...")
        
        segments = []
        
        # Extract each segment type
        for seg_type, patterns in self.SEGMENT_PATTERNS.items():
            type_segments = self._extract_segment_type(pages_dict, seg_type, patterns)
            segments.extend(type_segments)
        
        print(f"   ✓ Extracted {len(segments)} revenue segments")
        
        return segments
    
    def _extract_segment_type(
        self,
        pages_dict: Dict[int, str],
        seg_type: str,
        patterns: List[str]
    ) -> List[RevenueSegment]:
        """Extract segments of a specific type"""
        segments = []
        
        for page_num, text in pages_dict.items():
            text_lower = text.lower()
            
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    # Found segment disclosure page
                    # Extract segment names from this page
                    segment_names = self._extract_segment_names(text, seg_type)
                    
                    for name in segment_names:
                        segments.append(RevenueSegment(
                            name=name,
                            type=seg_type,
                            pages=[page_num],
                            revenue_data={},
                            has_detailed_split=True
                        ))
        
        return segments
    
    def _extract_segment_names(self, text: str, seg_type: str) -> List[str]:
        """Extract segment names from text"""
        names = []
        
        if seg_type == 'industry':
            # Look for industry names
            industry_keywords = [
                'automotive', 'pharmaceutical', 'fmcg', 'textile',
                'chemical', 'electronics', 'construction', 'healthcare',
                'toys', 'appliances', 'consumer durables', 'farm equipment'
            ]
            
            for keyword in industry_keywords:
                if keyword in text.lower():
                    names.append(keyword.title())
        
        elif seg_type == 'geography':
            # Look for geographic indicators
            if 'domestic' in text.lower():
                names.append('Domestic')
            if 'export' in text.lower():
                names.append('Export')
        
        return names


# ============================================================================
# ENTITY EXTRACTOR
# ============================================================================

class EntityExtractor:
    """
    Extracts business entities
    
    Types:
    - Suppliers/Vendors
    - Customers/Distributors
    - Subsidiaries/Associates
    - Related parties
    """
    
    ENTITY_PATTERNS = {
        'supplier': r'(?:supplier|vendor)[\s:]+([A-Z][A-Za-z\s&]+(?:Limited|Ltd|Pvt|Inc|Corp))',
        'customer': r'(?:customer|client)[\s:]+([A-Z][A-Za-z\s&]+(?:Limited|Ltd|Pvt|Inc|Corp))',
        'distributor': r'(?:distributor|dealer)[\s:]+([A-Z][A-Za-z\s&]+)',
        'subsidiary': r'(?:subsidiary|associate)[\s:]+([A-Z][A-Za-z\s&]+(?:Limited|Ltd|Pvt))',
    }
    
    RELATIONSHIP_PATTERNS = {
        'exclusive': r'exclusive',
        'key': r'key|principal|major',
        'related_party': r'related\s+part(?:y|ies)',
        'chinese': r'chinese|china',
    }
    
    def __init__(self):
        print("✅ Entity Extractor initialized")
    
    def extract_entities(self, pages_dict: Dict[int, str]) -> List[Entity]:
        """Extract all business entities"""
        print("\n🏢 Extracting business entities...")
        
        entities = []
        
        for page_num, text in pages_dict.items():
            # Extract each entity type
            for entity_type, pattern in self.ENTITY_PATTERNS.items():
                matches = re.finditer(pattern, text, re.IGNORECASE)
                
                for match in matches:
                    entity_name = match.group(1).strip()
                    
                    # Get context for relationship
                    start = max(0, match.start() - 100)
                    end = min(len(text), match.end() + 100)
                    context = text[start:end].lower()
                    
                    # Detect relationship
                    relationship = 'standard'
                    for rel_type, rel_pattern in self.RELATIONSHIP_PATTERNS.items():
                        if re.search(rel_pattern, context):
                            relationship = rel_type
                            break
                    
                    entities.append(Entity(
                        name=entity_name,
                        type=entity_type,
                        relationship=relationship,
                        pages=[page_num]
                    ))
        
        # Deduplicate
        entities = self._deduplicate_entities(entities)
        
        print(f"   ✓ Extracted {len(entities)} business entities")
        
        return entities
    
    def _deduplicate_entities(self, entities: List[Entity]) -> List[Entity]:
        """Remove duplicate entities"""
        seen = {}
        
        for entity in entities:
            key = entity.name.lower().strip()
            
            if key not in seen:
                seen[key] = entity
            else:
                # Merge pages
                seen[key].pages.extend(entity.pages)
                seen[key].pages = sorted(list(set(seen[key].pages)))
        
        return list(seen.values())


# ============================================================================
# PAGE MAPPING ENGINE
# ============================================================================

class PageMappingEngine:
    """
    Maps which pages discuss which topics
    
    Creates index:
    {
        'revenue_tables': [145, 146],
        'competition': [170],
        'business_overview': [150-160],
        'risk_factors': [20-35],
        ...
    }
    """
    
    TOPIC_PATTERNS = {
        'revenue_tables': [
            r'revenue.*break[\s-]*up',
            r'product[\s-]*wise.*revenue',
            r'segment[\s-]*wise.*revenue'
        ],
        'competition': [
            r'competition',
            r'competitive\s+landscape',
            r'market\s+position'
        ],
        'business_overview': [
            r'our\s+business',
            r'business\s+overview',
            r'about\s+(?:our\s+)?business'
        ],
        'risk_factors': [
            r'risk\s+factors',
            r'risks?\s+relating\s+to'
        ],
        'financial_statements': [
            r'financial\s+information',
            r'restated\s+financial',
            r'statement\s+of\s+(?:assets|profit)'
        ],
        'management': [
            r'our\s+management',
            r'board\s+of\s+directors',
            r'key\s+managerial\s+personnel'
        ],
        'properties': [
            r'propert(?:y|ies)',
            r'(?:manufacturing\s+)?(?:facilities|plants)'
        ],
        'licenses': [
            r'licenses?|approvals?',
            r'regulatory\s+clearances?'
        ],
    }
    
    def __init__(self):
        print("✅ Page Mapping Engine initialized")
    
    def create_page_map(self, pages_dict: Dict[int, str]) -> Dict[str, List[int]]:
        """Create topic → page number mapping"""
        print("\n📍 Creating page topic map...")
        
        page_map = defaultdict(list)
        
        for topic, patterns in self.TOPIC_PATTERNS.items():
            for page_num, text in pages_dict.items():
                text_lower = text.lower()
                
                for pattern in patterns:
                    if re.search(pattern, text_lower):
                        page_map[topic].append(page_num)
                        break  # Don't add same page twice for same topic
        
        # Convert to regular dict and sort pages
        page_map = {
            topic: sorted(list(set(pages)))
            for topic, pages in page_map.items()
        }
        
        print(f"   ✓ Mapped {len(page_map)} topics")
        for topic, pages in page_map.items():
            if pages:
                page_range = f"{pages[0]}-{pages[-1]}" if len(pages) > 1 else str(pages[0])
                print(f"      • {topic}: pages {page_range}")
        
        return dict(page_map)


# ============================================================================
# MASTER CONTENT EXTRACTION ENGINE
# ============================================================================

class ContentExtractionEngine:
    """
    Master orchestrator for content extraction
    
    Extracts complete DRHP-specific context:
    - Products
    - Segments
    - Financial trends
    - Entities
    - Page mappings
    
    This context is then fed to System B and Dimensions for
    DRHP-specific query generation.
    """
    
    def __init__(self):
        self.product_extractor = ProductExtractor()
        self.trend_analyzer = FinancialTrendAnalyzer()
        self.segment_extractor = SegmentExtractor()
        self.entity_extractor = EntityExtractor()
        self.page_mapper = PageMappingEngine()
        
        print("\n✅ Content Extraction Engine initialized")
    
    def extract_complete_context(
        self,
        pages_dict: Dict[int, str]
    ) -> Dict[str, Any]:
        """
        Extract complete DRHP context
        
        Args:
            pages_dict: {page_num: page_text}
        
        Returns:
            Complete context dictionary
        """
        print(f"\n{'='*80}")
        print(f"🔍 CONTENT EXTRACTION ENGINE")
        print(f"{'='*80}")
        print(f"Extracting context from {len(pages_dict)} pages...")
        
        # Extract products
        products = self.product_extractor.extract_products(pages_dict)
        
        # Analyze financial trends
        trends = self.trend_analyzer.analyze_trends(products, pages_dict)
        
        # Extract segments
        segments = self.segment_extractor.extract_segments(pages_dict)
        
        # Extract entities
        entities = self.entity_extractor.extract_entities(pages_dict)
        
        # Create page map
        page_map = self.page_mapper.create_page_map(pages_dict)
        
        # Helper to extract global context flags
        full_text = " ".join(pages_dict.values()).lower()
        
        # 1. Imports Analysis
        # Check for 'import', 'cif value', 'foreign currency', 'overseas'
        import_pattern = r'(import|foreign purchase|overseas purchase|cif value|foreign currency)'
        has_imports = bool(re.search(import_pattern, full_text))
        
        has_country_import_split = bool(re.search(r'(country[- ]wise.*import|import.*country[- ]wise)', full_text))
        
        # 2. Domestic Purchase Analysis
        # Check for 'domestic', 'local', 'indigenous', 'raw material'
        domestic_pattern = r'(domestic purchase|local purchase|indigenous|raw material|input material)'
        has_domestic_purchases = bool(re.search(domestic_pattern, full_text))
        
        has_state_purchase_split = bool(re.search(r'(state[- ]wise.*purchase|purchase.*state[- ]wise)', full_text))
        
        # 3. Manufacturing Process Text
        # Look for "manufacturing process", "process flow", "flow chart"
        mfg_keywords = ["manufacturing process", "process flow", "flow chart", "production process"]
        mfg_pages = [text for text in pages_dict.values() if any(k in text.lower() for k in mfg_keywords)]
        manufacturing_process_text = " ".join(mfg_pages) if mfg_pages else ""
        
        has_scrap_details = bool(re.search(r'(scrap|wastage|by-product|waste)', manufacturing_process_text, re.IGNORECASE))

        # Build context dictionary
        context = {
            'products': [self._product_to_dict(p) for p in products],
            'segments': [self._segment_to_dict(s) for s in segments],
            'trends': [self._trend_to_dict(t) for t in trends],
            'entities': [self._entity_to_dict(e) for e in entities],
            'page_map': page_map,
            'has_imports': has_imports,
            'has_country_import_split': has_country_import_split,
            'has_domestic_purchases': has_domestic_purchases,
            'has_state_purchase_split': has_state_purchase_split,
            'manufacturing_process': manufacturing_process_text,
            'has_scrap_details': has_scrap_details,
            'metadata': {
                'total_pages': len(pages_dict),
                'products_count': len(products),
                'segments_count': len(segments),
                'anomalies_count': len([t for t in trends if t.is_anomaly]),
                'entities_count': len(entities)
            }
        }
        
        print(f"\n✅ Context extraction complete")
        print(f"   Products: {len(products)}")
        print(f"   Segments: {len(segments)}")
        print(f"   Trends: {len(trends)} ({len([t for t in trends if t.is_anomaly])} anomalies)")
        print(f"   Entities: {len(entities)}")
        print(f"   Topic pages mapped: {len(page_map)}")
        print(f"   Imports detected: {has_imports} (Split: {has_country_import_split})")
        print(f"   Domestic Purchases: {has_domestic_purchases} (Split: {has_state_purchase_split})")
        print(f"{'='*80}\n")
        
        return context
    
    def _product_to_dict(self, product: Product) -> Dict:
        """Convert Product to dictionary"""
        return {
            'name': product.name,
            'category': product.category,
            'pages': product.mentioned_pages,
            'revenue_data': product.revenue_data,
            'export_split_disclosed': product.export_split_disclosed,
            'sku_count': product.sku_count
        }
    
    def _segment_to_dict(self, segment: RevenueSegment) -> Dict:
        """Convert RevenueSegment to dictionary"""
        return {
            'name': segment.name,
            'type': segment.type,
            'pages': segment.pages,
            'revenue_data': segment.revenue_data,
            'has_detailed_split': segment.has_detailed_split
        }
    
    def _trend_to_dict(self, trend: FinancialTrend) -> Dict:
        """Convert FinancialTrend to dictionary"""
        return {
            'metric': trend.metric,
            'entity': trend.entity,
            'fy_data': trend.fy_data,
            'change_pct': round(trend.change_pct, 2),
            'is_anomaly': trend.is_anomaly,
            'pages': trend.pages
        }
    
    def _entity_to_dict(self, entity: Entity) -> Dict:
        """Convert Entity to dictionary"""
        return {
            'name': entity.name,
            'type': entity.type,
            'relationship': entity.relationship,
            'pages': entity.pages,
            'financial_dependency': entity.financial_dependency
        }


def get_content_extraction_engine():
    """Factory function"""
    return ContentExtractionEngine()