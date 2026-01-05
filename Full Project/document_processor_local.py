"""
Local PDF Processor - Replacement for GCP Document AI
=====================================================
Uses pdfplumber for local PDF text extraction with page-level precision.

Key Features:
- No GCP dependencies
- Page-by-page text extraction
- Table detection and extraction
- Multi-column support
- Preserves page numbers
- Local file processing

Install:
pip install pdfplumber --break-system-packages
"""

import os
import json
from typing import Dict, List, Any
import pdfplumber
from pathlib import Path


class LocalPDFProcessor:
    """
    Local PDF processor using pdfplumber
    Replacement for GCP Document AI
    """
    
    def __init__(self):
        """Initialize PDF processor"""
        print("✅ Local PDF Processor initialized (pdfplumber)")
    
    def process_pdf_from_path(self, file_path: str) -> Dict[str, Any]:
        """
        Process PDF from local file path
        
        Args:
            file_path: Local path to PDF file
        
        Returns:
            dict: Processed document with text and page mapping
        """
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        print(f"📄 Processing PDF: {file_path}")
        
        pages_data = []
        full_text = ""
        
        try:
            with pdfplumber.open(file_path) as pdf:
                total_pages = len(pdf.pages)
                print(f"   Total pages: {total_pages}")
                
                for page_num, page in enumerate(pdf.pages, start=1):
                    # Extract text from page
                    page_text = self._extract_page_text(page, page_num)
                    
                    # Extract tables if any
                    tables = self._extract_tables(page, page_num)
                    
                    pages_data.append({
                        'page_number': page_num,
                        'text': page_text,
                        'word_count': len(page_text.split()),
                        'has_tables': len(tables) > 0,
                        'table_count': len(tables),
                        'tables': tables
                    })
                    
                    full_text += page_text + "\n\n"
                    
                    if page_num % 10 == 0:
                        print(f"   Processed {page_num}/{total_pages} pages...")
        
        except Exception as e:
            print(f"❌ Error processing PDF: {e}")
            raise
        
        print(f"✅ Extracted text from {len(pages_data)} pages")
        
        return {
            'full_text': full_text.strip(),
            'pages': pages_data,
            'total_pages': len(pages_data)
        }
    
    def _extract_page_text(self, page, page_num: int) -> str:
        """
        Extract text from a single page with multi-column support
        
        Args:
            page: pdfplumber page object
            page_num: Page number for logging
        
        Returns:
            str: Extracted text
        """
        try:
            # Try layout-preserving extraction first
            text = page.extract_text(layout=True)
            
            if not text or len(text.strip()) < 50:
                # Fallback: basic extraction
                text = page.extract_text()
            
            if not text:
                # Fallback: extract words and join
                words = page.extract_words()
                if words:
                    text = " ".join([w['text'] for w in words])
            
            return text.strip() if text else ""
        
        except Exception as e:
            print(f"   ⚠️  Warning: Could not extract text from page {page_num}: {e}")
            return ""
    
    def _extract_tables(self, page, page_num: int) -> List[Dict[str, Any]]:
        """
        Extract tables from page
        
        Args:
            page: pdfplumber page object
            page_num: Page number for logging
        
        Returns:
            list: Extracted tables with metadata
        """
        tables = []
        
        try:
            extracted_tables = page.extract_tables()
            
            for idx, table in enumerate(extracted_tables):
                if table and len(table) > 0:
                    # Clean table data
                    cleaned_table = [
                        [cell.strip() if cell else "" for cell in row]
                        for row in table
                    ]
                    
                    # Convert to text representation
                    table_text = self._table_to_text(cleaned_table)
                    
                    tables.append({
                        'table_id': f"page_{page_num}_table_{idx+1}",
                        'rows': len(cleaned_table),
                        'columns': len(cleaned_table[0]) if cleaned_table else 0,
                        'data': cleaned_table,
                        'text': table_text
                    })
        
        except Exception as e:
            print(f"   ⚠️  Warning: Could not extract tables from page {page_num}: {e}")
        
        return tables
    
    def _table_to_text(self, table: List[List[str]]) -> str:
        """Convert table to readable text format"""
        if not table:
            return ""
        
        lines = []
        for row in table:
            line = " | ".join(row)
            lines.append(line)
        
        return "\n".join(lines)


def process_pdf_with_docai(file_path: str) -> Dict[str, Any]:
    """
    Main function - compatible with old GCP interface
    
    Args:
        file_path: Can be local path OR gs:// URI (will convert)
    
    Returns:
        dict: Processed document with text and page mapping
    """
    
    # Handle GCS URIs (convert to local if needed)
    if file_path.startswith('gs://'):
        # Extract filename
        filename = file_path.split('/')[-1]
        # Assume it's in current directory or uploads
        local_path = f"./uploads/{filename}"
        
        if not os.path.exists(local_path):
            raise FileNotFoundError(
                f"GCS URI provided but local file not found: {local_path}\n"
                f"Please download the file first or use local path"
            )
        
        file_path = local_path
    
    # Process with local processor
    processor = LocalPDFProcessor()
    return processor.process_pdf_from_path(file_path)


def chunk_document(pages_data: List[Dict], chunk_size: int = 1000, overlap: int = 200) -> List[Dict]:
    """
    Create overlapping chunks from pages while preserving page numbers
    
    Args:
        pages_data: List of page dictionaries
        chunk_size: Characters per chunk
        overlap: Overlap between chunks
    
    Returns:
        list: Chunks with metadata
    """
    chunks = []
    chunk_id = 0
    
    for page in pages_data:
        page_num = page['page_number']
        text = page['text']
        
        if not text.strip():
            continue
        
        # Split page into chunks if it's long
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end]
            
            if chunk_text.strip():
                chunks.append({
                    'chunk_id': chunk_id,
                    'text': chunk_text,
                    'page_number': page_num,
                    'start_pos': start,
                    'end_pos': end,
                    'has_tables': page.get('has_tables', False)
                })
                chunk_id += 1
            
            start = end - overlap  # Create overlap
    
    return chunks


# ============================================================================
# BACKWARD COMPATIBILITY LAYER
# ============================================================================

class DocumentProcessor:
    """
    Document processor class for backward compatibility
    Matches the interface your code expects
    """
    
    def __init__(self):
        self.processor = LocalPDFProcessor()
    
    def process_pdf_with_pages(self, file_path: str) -> List[Dict]:
        """
        Process PDF and return chunks with page numbers
        
        Args:
            file_path: Path to PDF file
        
        Returns:
            list: Document chunks with page metadata
        """
        # Process PDF
        result = self.processor.process_pdf_from_path(file_path)
        
        # Create chunks
        chunks = chunk_document(
            pages_data=result['pages'],
            chunk_size=1000,
            overlap=200
        )
        
        return chunks
    
    def extract_text_with_pages(self, file_path: str) -> Dict[str, Any]:
        """
        Extract text with page-level granularity
        
        Args:
            file_path: Path to PDF file
        
        Returns:
            dict: Full result with pages
        """
        return self.processor.process_pdf_from_path(file_path)


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """Test the local PDF processor"""
    
    print("="*80)
    print("🧪 TESTING LOCAL PDF PROCESSOR")
    print("="*80)
    
    # Test file path
    test_file = "./test.pdf"
    
    if not os.path.exists(test_file):
        print(f"\n⚠️  Test file not found: {test_file}")
        print("   Create a test PDF file or update the path")
    else:
        # Test 1: Full processing
        print("\n[TEST 1] Full PDF Processing")
        print("-"*80)
        
        result = process_pdf_with_docai(test_file)
        print(f"✅ Processed {result['total_pages']} pages")
        print(f"✅ Total text length: {len(result['full_text'])} chars")
        
        if result['pages']:
            print(f"\nFirst page preview:")
            print(result['pages'][0]['text'][:300])
            print("...")
        
        # Test 2: Chunking
        print("\n[TEST 2] Document Chunking")
        print("-"*80)
        
        chunks = chunk_document(result['pages'], chunk_size=500, overlap=100)
        print(f"✅ Created {len(chunks)} chunks")
        
        if chunks:
            print(f"\nFirst chunk:")
            print(f"  Page: {chunks[0]['page_number']}")
            print(f"  Text: {chunks[0]['text'][:200]}...")
        
        # Test 3: Table detection
        print("\n[TEST 3] Table Detection")
        print("-"*80)
        
        pages_with_tables = [p for p in result['pages'] if p.get('has_tables')]
        print(f"✅ Found {len(pages_with_tables)} pages with tables")
        
        if pages_with_tables:
            for page in pages_with_tables[:3]:  # Show first 3
                print(f"\nPage {page['page_number']}: {page['table_count']} table(s)")
        
        # Test 4: Backward compatibility
        print("\n[TEST 4] Backward Compatibility Interface")
        print("-"*80)
        
        processor = DocumentProcessor()
        chunks = processor.process_pdf_with_pages(test_file)
        print(f"✅ DocumentProcessor.process_pdf_with_pages() works")
        print(f"   Returned {len(chunks)} chunks")
    
    print("\n" + "="*80)
    print("✅ LOCAL PDF PROCESSOR TEST COMPLETE")
    print("="*80)