# engines/engine_1_doc_intel.py

import re
try:
    import pdfplumber
except ImportError:
    pdfplumber = None

class DocumentIntelligenceEngine:
    """
    ENGINE 1: Document Intelligence
    Responsible for:
    - Loading the PDF
    - Extracting text page-wise
    - Identify basic structures (tables, headers)
    """

    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.pages = {} # {page_num: text}
        self.tables = {} # {page_num: [table_data...]}
        self.metadata = {}

    def process(self):
        """
        Main processing function to extract content.
        """
        print(f"[*] Engine 1: Processing PDF {self.pdf_path}...")
        
        if pdfplumber:
            try:
                with pdfplumber.open(self.pdf_path) as pdf:
                    self.metadata = pdf.metadata
                    for i, page in enumerate(pdf.pages):
                        page_num = i + 1
                        text = page.extract_text() or ""
                        self.pages[page_num] = text
                        
                        # Basic table extraction
                        tables = page.extract_tables()
                        if tables:
                            self.tables[page_num] = tables
                            
                print(f"[*] Extracted {len(self.pages)} pages.")
            except Exception as e:
                print(f"[!] Error reading PDF: {e}")
                self._load_fallback_data()
        else:
            print("[!] pdfplumber not found. Using fallback text for demonstration.")
            self._load_fallback_data()

        # SEGMENTATION LOGIC
        # Filter pages to only include the target chapter
        target_pages = self._segment_by_chapter()
        
        return {
            "pages": target_pages, # Only return pages for the requested chapter
            "tables": self.tables,
            "metadata": self.metadata
        }

    def _extract_printed_page_number(self, text, physical_page_num):
        """
        Attempt to find the actual printed page number from headers/footers.
        Checks multiple locations and formats.
        """
        lines = text.strip().split('\n')
        if not lines:
            return physical_page_num
        
        # Strategy 1: Check footer (last 3 lines) for standalone numbers
        for line in lines[-3:]:
            # Standalone number pattern
            match = re.search(r'^\s*(\d+)\s*$', line.strip())
            if match:
                page_num = int(match.group(1))
                # Sanity check: page number should be reasonable (1-500 for most DRHPs)
                if 1 <= page_num <= 500:
                    return page_num
        
        # Strategy 2: Check header (first 3 lines) for "Page X" or "X" format
        for line in lines[:3]:
            # "Page 123" or "Page: 123" format
            match = re.search(r'(?:Page|Pg\.?)\s*:?\s*(\d+)', line, re.IGNORECASE)
            if match:
                page_num = int(match.group(1))
                if 1 <= page_num <= 500:
                    return page_num
        
        # Strategy 3: Look for page numbers with surrounding text (e.g., "| 123 |")
        footer_text = ' '.join(lines[-3:])
        match = re.search(r'[|\s](\d+)[|\s]', footer_text)
        if match:
            page_num = int(match.group(1))
            if 1 <= page_num <= 500:
                return page_num
        
        # Fallback: Use physical page number
        return physical_page_num

    def _segment_by_chapter(self):
        """
        Identify and extract only the pages belonging to the target chapter.
        Uses multiple strategies for robust chapter isolation.
        """
        relevant_pages = {}
        in_chapter = False
        
        # ENHANCED: Multiple patterns for Business Overview detection
        start_patterns = [
            re.compile(r"(SECTION|CHAPTER).*?(?:VI|6).*?(?:BUSINESS|OUR\s+BUSINESS)", re.IGNORECASE),
            re.compile(r"(?:BUSINESS\s+OVERVIEW|OUR\s+BUSINESS|INDUSTRY\s+OVERVIEW|COMPANY\s+OVERVIEW)", re.IGNORECASE),
            re.compile(r"(?:^|\n)\s*(?:VI|6)\.?\s*(?:BUSINESS|OUR\s+BUSINESS)", re.IGNORECASE | re.MULTILINE)
        ]
        
        # ENHANCED: Patterns to detect END of Business Overview (start of next section)
        end_patterns = [
            re.compile(r"(SECTION|CHAPTER).*?(?:VII|7|VIII|8).*?(?:REGULATIONS|MANAGEMENT|FINANCIAL|RISK)", re.IGNORECASE),
            re.compile(r"(?:^|\n)\s*(?:RISK\s+FACTORS|KEY\s+REGULATIONS|MANAGEMENT.*?DISCUSSION|FINANCIAL\s+INFORMATION|LEGAL\s+PROCEEDINGS|OUTSTANDING\s+LITIGATION)", re.IGNORECASE | re.MULTILINE)
        ]
        
        # NEW: Keywords that indicate contamination from other chapters
        contamination_keywords = [
            r"risk\s+factor",
            r"material\s+litigation",
            r"legal\s+proceedings?",
            r"auditor'?s?\s+report",
            r"financial\s+statement",
            r"balance\s+sheet",
            r"profit\s+(?:and|\&)\s+loss",
            r"cash\s+flow\s+statement",
            r"related\s+party\s+transactions?\s+note",  # From notes to accounts
        ]
        contamination_pattern = re.compile('|'.join(contamination_keywords), re.IGNORECASE)
        
        # NEW: Keywords that strongly indicate business content
        business_keywords = [
            r"(?:our|the)?\s*(?:products?|services?)",
            r"manufacturing",
            r"revenue\s+from\s+operations",
            r"customers?",
            r"distributors?",
            r"market\s+share",
            r"capacity\s+utili[sz]ation",
        ]
        business_pattern = re.compile('|'.join(business_keywords), re.IGNORECASE)
        
        found_start = False
        sorted_p_nums = sorted(self.pages.keys())
        
        print("[*] Engine 1: Segmenting 'Business Overview' chapter...")
        
        for p_num in sorted_p_nums:
            text = self.pages[p_num]
            doc_page_num = self._extract_printed_page_number(text, p_num)
            
            # Check for Chapter Start
            if not in_chapter:
                # Look in first 10 lines for chapter header
                header_text = "\n".join(text.split('\n')[:10])
                for pattern in start_patterns:
                    if pattern.search(header_text):
                        print(f"[*] Found 'Business Overview' START at Physical Page {p_num} (Printed Page {doc_page_num})")
                        in_chapter = True
                        found_start = True
                        break
            
            # Check for Chapter End (only if inside chapter)
            elif in_chapter:
                header_text = "\n".join(text.split('\n')[:10])
                for pattern in end_patterns:
                    if pattern.search(header_text):
                        print(f"[*] Found 'Business Overview' END at Physical Page {p_num} (Printed Page {doc_page_num})")
                        in_chapter = False
                        break
            
            # If we're in the chapter, validate page purity
            if in_chapter:
                # Strategy 1: Check for contamination keywords
                contamination_matches = len(contamination_pattern.findall(text))
                business_matches = len(business_pattern.findall(text))
                
                # Accept page if:
                # - Low contamination (<3 matches) OR
                # - Business keywords dominate (ratio > 2:1)
                is_pure = contamination_matches < 3 or (business_matches / max(contamination_matches, 1) >= 2)
                
                if is_pure:
                    relevant_pages[doc_page_num] = text
                else:
                    print(f"[!] Filtered contaminated page {doc_page_num} (Contam: {contamination_matches}, Business: {business_matches})")
        
        # Fallback handling
        if not found_start:
            print("[!] Could not detect 'Business Overview' boundaries. Attempting keyword-based filtering...")
            # Use keyword density to filter business-related pages
            filtered_pages = {}
            for p_num in sorted_p_nums:
                text = self.pages[p_num]
                doc_p_num = self._extract_printed_page_number(text, p_num)
                
                # Include page if it has strong business keywords and low contamination
                business_score = len(business_pattern.findall(text))
                contamination_score = len(contamination_pattern.findall(text))
                
                if business_score >= 3 and contamination_score < 5:
                    filtered_pages[doc_p_num] = text
                    print(f"[*] Included page {doc_p_num} based on keywords (B:{business_score}, C:{contamination_score})")
            
            if filtered_pages:
                print(f"[*] Fallback filtering found {len(filtered_pages)} business-related pages")
                return filtered_pages
            else:
                print("[!] Fallback filtering failed. Returning all pages with proper numbering.")
                # Last resort: return all pages with proper page numbers
                mapped_pages = {}
                for p_num in sorted_p_nums:
                    text = self.pages[p_num]
                    doc_p_num = self._extract_printed_page_number(text, p_num)
                    mapped_pages[doc_p_num] = text
                return mapped_pages
        
        print(f"[*] Extracted {len(relevant_pages)} pages for 'Business Overview'")
        return relevant_pages

    def _load_fallback_data(self):
        """
        Fallback data for testing/demo if PDF processing fails or lib missing.
        Simulates a Business Overview chapter.
        """
        # Simulating a snippet of a DRHP Business Overview
        self.pages[131] = """
        CHAPTER VI: BUSINESS OVERVIEW
        
        Our Company is a leading manufacturer of widgets in India. We have 3 manufacturing units.
        Our revenue for fiscal 2024 was Rs. 500 Crores. 
        We rely on imported raw materials for our premium segment.
        """
        self.pages[132] = """
        We have a strong marketing strategy focusing on digital channels.
        Our capacity utilization was 55% in the last year due to market slowdown.
        We have 500 employees. We face high attrition in the sales team.
        """
        self.pages[133] = """
        Our Top 10 customers contribute 60% of our revenue.
        We do not have long term agreements with our suppliers.
        """
        self.pages[134] = """
        SECTION 2: COMPETITION
        
        We compete with large multinational corporations.
        Our market share is estimated to be 15%.
        """

    def get_text_for_page(self, page_num):
        return self.pages.get(page_num, "")

    def get_all_text(self):
        return "\n".join(self.pages.values())
