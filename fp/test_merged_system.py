#!/usr/bin/env python3
"""
Test Script for Merged NSE Engine System
=========================================

Tests the integration of SystemB's engines with SystemA's architecture.

Usage:
    python test_merged_system.py --pdf path/to/drhp.pdf --chapter "Business Overview"
"""

import argparse
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# If this module is imported by pytest during collection, skip it because
# it's an integration test script intended to be run directly, not as
# a unit-test module. When run as a script (__main__), do not skip.
if __name__ != "__main__":
    try:
        import pytest
        pytest.skip("Integration script; not a pytest test module", allow_module_level=True)
    except Exception:
        # If pytest isn't available or skip fails, continue without skipping
        pass

from nse_engine_adapter import get_nse_engine_adapter
from engines.engine_1_doc_intel import DocumentIntelligenceEngine
from engines.engine_3_content_review import ContentReviewEngine
from nse_output_formatter import format_nse_letter_style, format_for_api_response


def test_engine_1_page_extraction(pdf_path):
    """Test Engine 1: Document Intelligence"""
    print("\n" + "="*80)
    print("TEST 1: ENGINE 1 - PAGE EXTRACTION")
    print("="*80)
    
    engine = DocumentIntelligenceEngine(pdf_path)
    doc_data = engine.process()
    
    pages = doc_data['pages']
    
    print(f"\n✅ Extracted {len(pages)} pages")
    print(f"✅ Page numbers range: {min(pages.keys())} to {max(pages.keys())}")
    
    # Sample first 3 pages
    print(f"\n📄 Sample Pages:")
    for page_num in sorted(pages.keys())[:3]:
        text_preview = pages[page_num][:150].replace('\n', ' ')
        print(f"  Page {page_num}: {text_preview}...")
    
    # Check if page numbers are realistic (not all 0s or 1s)
    unique_pages = len(set(pages.keys()))
    if unique_pages > 1:
        print(f"\n✅ PASS: Page numbers are properly extracted ({unique_pages} unique pages)")
    else:
        print(f"\n❌ FAIL: Page numbers may be incorrect (only {unique_pages} unique page number)")
    
    return doc_data


def test_engine_3_content_review(doc_data, chapter_name):
    """Test Engine 3: Content Review"""
    print("\n" + "="*80)
    print("TEST 2: ENGINE 3 - CONTENT REVIEW")
    print("="*80)
    
    engine = ContentReviewEngine(doc_data, chapter_name)
    queries = engine.generate_queries(doc_data['pages'])
    
    print(f"\n✅ Generated {len(queries)} queries")
    
    # Check query structure
    if queries:
        sample_query = queries[0]
        print(f"\n📋 Sample Query Structure:")
        print(f"  Keys: {list(sample_query.keys())}")
        
        # Verify essential fields
        has_page = 'page' in sample_query
        has_text = 'text' in sample_query
        has_issue_id = 'issue_id' in sample_query
        has_severity = 'severity' in sample_query
        
        print(f"\n  ✓ Has page: {has_page}")
        print(f"  ✓ Has text: {has_text}")
        print(f"  ✓ Has issue_id: {has_issue_id}")
        print(f"  ✓ Has severity: {has_severity}")
        
        if all([has_page, has_text, has_issue_id, has_severity]):
            print(f"\n✅ PASS: Query structure is complete")
        else:
            print(f"\n⚠️  WARNING: Query structure may be incomplete")
        
        # Show first 3 queries
        print(f"\n📋 First 3 Queries:")
        for i, q in enumerate(queries[:3], 1):
            print(f"\n  Query {i}:")
            print(f"    Page: {q.get('page', 'N/A')}")
            print(f"    Issue ID: {q.get('issue_id', 'N/A')}")
            print(f"    Severity: {q.get('severity', 'N/A')}")
            print(f"    Text: {q.get('text', '')[:100]}...")
    
    return queries


def test_nse_adapter(pdf_path, chapter_name):
    """Test NSE Engine Adapter (full integration)"""
    print("\n" + "="*80)
    print("TEST 3: NSE ENGINE ADAPTER - FULL INTEGRATION")
    print("="*80)
    
    adapter = get_nse_engine_adapter()
    
    # Simulate chunks (in real integration, these come from document_processor_local.py)
    # For testing, we'll pass pdf_path directly
    print(f"\n📄 Processing: {pdf_path}")
    print(f"📖 Chapter: {chapter_name}")
    
    queries = adapter.analyze_business_chapter(
        drhp_chunks=[],  # Empty for test - adapter will use pdf_path
        company_name="Test Company Ltd.",
        company_profile={'revenue': 500, 'employees': 200, 'business_type': 'Manufacturing'},
        pdf_path=pdf_path,
        chapter_name=chapter_name
    )
    
    print(f"\n✅ Generated {len(queries)} enhanced queries")
    
    # Verify enhanced structure
    if queries:
        sample_query = queries[0]
        print(f"\n📋 Enhanced Query Structure:")
        print(f"  Keys: {list(sample_query.keys())}")
        
        # Verify SystemA-compatible format
        has_regulation = 'regulation_ref' in sample_query
        has_category = 'category' in sample_query
        has_observation = 'observation' in sample_query
        
        print(f"\n  ✓ Has regulation_ref: {has_regulation}")
        print(f"  ✓ Has category: {has_category}")
        print(f"  ✓ Has observation: {has_observation}")
        
        if all([has_regulation, has_category, has_observation]):
            print(f"\n✅ PASS: Enhanced query structure is SystemA-compatible")
        else:
            print(f"\n❌ FAIL: Enhanced query structure is incomplete")
        
        # Show sample with regulation references
        print(f"\n📋 Sample Enhanced Queries:")
        for i, q in enumerate(queries[:3], 1):
            print(f"\n  Query {i}:")
            print(f"    Page: {q.get('page', 'N/A')}")
            print(f"    Severity: {q.get('severity', 'N/A')}")
            print(f"    Category: {q.get('category', 'N/A')}")
            print(f"    Regulation: {q.get('regulation_ref', 'N/A')}")
            print(f"    Observation: {q.get('observation', '')[:120]}...")
    
    return queries


def test_output_formatting(queries, chapter_name):
    """Test Output Formatting"""
    print("\n" + "="*80)
    print("TEST 4: OUTPUT FORMATTING")
    print("="*80)
    
    # Test API format
    api_format = format_for_api_response(queries)
    print(f"\n✅ API Format: {len(api_format)} queries formatted")
    
    # Test letter format
    letter = format_nse_letter_style(queries, chapter_name=chapter_name)
    print(f"\n✅ Letter Format Generated ({len(letter)} characters)")
    
    # Show sample of letter format
    print(f"\n📄 Letter Format Preview:")
    print("-" * 80)
    print(letter[:800])
    print("-" * 80)
    
    # Check if format matches NSE style
    has_regulation_ref = 'Regulation Ref:' in letter
    has_page_numbers = 'Page' in letter
    has_severity = any(s in letter for s in ['Major', 'Minor', 'Critical'])
    
    print(f"\n  ✓ Has regulation references: {has_regulation_ref}")
    print(f"  ✓ Has page numbers: {has_page_numbers}")
    print(f"  ✓ Has severity levels: {has_severity}")
    
    if all([has_regulation_ref, has_page_numbers, has_severity]):
        print(f"\n✅ PASS: Output matches NSE letter format")
    else:
        print(f"\n⚠️  WARNING: Output may not match NSE format exactly")


def run_full_test(pdf_path, chapter_name):
    """Run complete test suite"""
    print("\n" + "="*80)
    print("MERGED NSE ENGINE SYSTEM - COMPREHENSIVE TEST")
    print("="*80)
    print(f"PDF: {pdf_path}")
    print(f"Chapter: {chapter_name}")
    
    try:
        # Test 1: Page Extraction
        doc_data = test_engine_1_page_extraction(pdf_path)
        
        # Test 2: Content Review
        raw_queries = test_engine_3_content_review(doc_data, chapter_name)
        
        # Test 3: NSE Adapter (full integration)
        enhanced_queries = test_nse_adapter(pdf_path, chapter_name)
        
        # Test 4: Output Formatting
        test_output_formatting(enhanced_queries, chapter_name)
        
        # Summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"✅ All tests completed")
        print(f"✅ Total queries generated: {len(enhanced_queries)}")
        print(f"✅ System is ready for integration into multi_agent_orchestrator.py")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED with error:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(description="Test Merged NSE Engine System")
    parser.add_argument("--pdf", required=True, help="Path to DRHP PDF file")
    parser.add_argument("--chapter", default="Business Overview", help="Chapter name to analyze")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.pdf):
        print(f"❌ Error: PDF file not found: {args.pdf}")
        sys.exit(1)
    
    success = run_full_test(args.pdf, args.chapter)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
