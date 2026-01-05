"""
Test the New Forensic Architecture
===================================
Comprehensive testing before full integration
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from forensic_orchestrator import get_forensic_orchestrator
from document_processor_local import DocumentProcessor
import json


def test_with_sample_text():
    """Test with hardcoded sample text"""
    
    print("="*80)
    print("🧪 TEST 1: Sample Text Detection")
    print("="*80)
    
    # Sample pages with various compliance issues
    pages_dict = {
        158: """
        Business Overview
        
        The Company imports CNG kits and components from Landi Renzo SpA, Italy 
        worth approximately €2 million annually. These imports are critical to 
        our manufacturing operations. The Company uses foreign currency for 
        all import transactions.
        
        Product-wise Revenue for FY2024:
        - Automotive segment: ₹125.5 crores
        - Industrial segment: ₹45.2 crores
        - Total Revenue: ₹170.7 crores
        
        The Company's revenue shows seasonal fluctuation due to monsoon dependency
        in the agricultural sector, with Q2 and Q3 accounting for 65% of annual revenue.
        """,
        
        159: """
        Capacity and Expansion Plans
        
        Current installed capacity: 30,000 units per annum
        Capacity utilization: 85% in FY2024
        
        Post-expansion (Objects of the Offer), the Company will have an installed 
        capacity of 50,000 units per annum. The expansion is expected to be 
        completed by Q2 FY2026.
        
        The Company has entered into a technical collaboration agreement with
        XYZ Technology Corporation for proprietary manufacturing processes.
        The collaboration includes licensing of patented technology.
        """,
        
        160: """
        Supply Chain and Manufacturing
        
        The Company procures raw materials domestically and internationally.
        Key suppliers include Chinese manufacturers for electronic components.
        
        Manufacturing Process:
        The Company follows a semi-automated production process. Scrap and
        wastage during manufacturing is approximately 3-5% of raw material input.
        
        Quality Assurance:
        The Company has ISO 9001:2015 certification and follows strict quality
        control measures.
        """
    }
    
    # Initialize orchestrator
    print(f"\n🚀 Initializing Forensic Orchestrator...")
    orchestrator = get_forensic_orchestrator()
    
    # Process
    print(f"\n🔬 Processing sample pages...")
    queries = orchestrator.process_drhp(pages_dict, "Business Overview")
    
    # Display results
    print(f"\n{'='*80}")
    print(f"📊 TEST 1 RESULTS")
    print(f"{'='*80}")
    print(f"Total queries generated: {len(queries)}")
    
    if queries:
        print(f"\n🎯 Detected Issues:")
        for i, query in enumerate(queries, 1):
            print(f"\n[{i}] Page {query['page']} - {query['severity']}")
            print(f"    Issue: {query['issue_id']}")
            print(f"    Category: {query['category']}")
            print(f"    Regulation: {query['regulation_ref']}")
            print(f"\n    Query Preview:")
            print(f"    {query['query'][:200]}...")
            print("-"*80)
    else:
        print("\n⚠️  No issues detected in sample text")
        print("   This might indicate patterns need tuning")
    
    return queries


def test_with_actual_pdf():
    """Test with actual DRHP PDF"""
    
    print("\n" + "="*80)
    print("🧪 TEST 2: Actual PDF Processing")
    print("="*80)
    
    pdf_path = input("\nEnter path to DRHP PDF (or press Enter to skip): ").strip()
    
    if not pdf_path or not os.path.exists(pdf_path):
        if pdf_path:
            print(f"❌ File not found: {pdf_path}")
        print("⏭️  Test 2 skipped")
        return None
    
    try:
        # Process PDF
        print(f"\n📄 Processing PDF...")
        processor = DocumentProcessor()
        result = processor.extract_text_with_pages(pdf_path)
        
        # Convert to pages_dict
        pages_dict = {}
        for page in result['pages']:
            pages_dict[page['page_number']] = page['text']
        
        print(f"   ✅ Loaded {len(pages_dict)} pages from PDF")
        
        # Limit to first 20 pages for testing
        if len(pages_dict) > 20:
            print(f"   ℹ️  Testing with first 20 pages only")
            pages_dict = {k: v for k, v in list(pages_dict.items())[:20]}
        
        # Process with forensic orchestrator
        print(f"\n🔬 Running forensic analysis...")
        orchestrator = get_forensic_orchestrator()
        queries = orchestrator.process_drhp(pages_dict, "Business Overview")
        
        # Display results
        print(f"\n{'='*80}")
        print(f"📊 TEST 2 RESULTS")
        print(f"{'='*80}")
        print(f"Total queries generated: {len(queries)}")
        
        if queries:
            # Show first 5
            print(f"\n🎯 First 5 Queries:")
            for i, query in enumerate(queries[:5], 1):
                print(f"\n[{i}] Page {query['page']} - {query['severity']}")
                print(f"    {query['query'][:150]}...")
                print("-"*80)
            
            if len(queries) > 5:
                print(f"\n... and {len(queries) - 5} more queries")
            
            # Save to file
            output_file = "forensic_test_output.json"
            with open(output_file, 'w') as f:
                json.dump(queries, f, indent=2)
            
            print(f"\n✅ Full output saved to: {output_file}")
        else:
            print("\n⚠️  No issues detected")
            print("   Possible reasons:")
            print("   - Document is fully compliant (unlikely)")
            print("   - Patterns not matching (check checklists.py)")
            print("   - Text extraction issues (check PDF quality)")
        
        return queries
    
    except Exception as e:
        print(f"\n❌ Error in Test 2: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_specific_patterns():
    """Test specific regex patterns"""
    
    print("\n" + "="*80)
    print("🧪 TEST 3: Pattern Matching Validation")
    print("="*80)
    
    test_cases = [
        {
            'text': 'The Company imports from Italy worth €2 million',
            'expected_issues': ['FOREX_HEDGING_POLICY'],
            'description': 'Foreign currency detection'
        },
        {
            'text': 'Revenue shows seasonal fluctuation due to monsoon',
            'expected_issues': ['SEASONALITY_DISCLOSURE'],
            'description': 'Seasonality detection'
        },
        {
            'text': 'Post-expansion, installed capacity will be 50,000 units',
            'expected_issues': ['PROPOSED_CAPACITY_BASIS'],
            'description': 'Capacity estimation detection'
        },
        {
            'text': 'Technical collaboration with XYZ for proprietary technology',
            'expected_issues': ['PATENT_VALIDITY_RISK'],
            'description': 'Patent/IP detection'
        }
    ]
    
    from forensic_scanner import get_forensic_scanner
    try:
        from data.checklists import NSE_ISSUES
    except ImportError:
        from data.checklists import NSE_ISSUES
    
    scanner = get_forensic_scanner(NSE_ISSUES)
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n[Test {i}] {test['description']}")
        print(f"   Text: \"{test['text'][:60]}...\"")
        
        findings = scanner.scan_page(test['text'], page_number=1)
        detected_issues = [f['issue_id'] for f in findings]
        
        # Check if expected issues were found
        found = any(exp in detected_issues for exp in test['expected_issues'])
        
        if found:
            print(f"   ✅ PASS - Detected: {detected_issues}")
            passed += 1
        else:
            print(f"   ❌ FAIL - Expected: {test['expected_issues']}")
            print(f"   Got: {detected_issues if detected_issues else 'Nothing'}")
            failed += 1
    
    print(f"\n{'='*80}")
    print(f"Pattern Test Results: {passed} passed, {failed} failed")
    print(f"{'='*80}")
    
    if failed > 0:
        print(f"\n⚠️  Some patterns failed")
        print(f"   Action: Check regex patterns in checklists.py")
    else:
        print(f"\n✅ All pattern tests passed!")


def compare_with_expected():
    """Compare with expected output"""
    
    print("\n" + "="*80)
    print("🧪 TEST 4: Accuracy Comparison")
    print("="*80)
    
    output_file = "forensic_test_output.json"
    
    if not os.path.exists(output_file):
        print(f"⏭️  Skipped - Run Test 2 first to generate output")
        return
    
    with open(output_file, 'r') as f:
        system_output = json.load(f)
    
    print(f"\nSystem generated: {len(system_output)} queries")
    
    # Manual comparison
    print(f"\n📋 Manual Review Required:")
    print(f"   1. Review forensic_test_output.json")
    print(f"   2. Compare with your expected queries PDF")
    print(f"   3. Count matches")
    print(f"\n   Expected accuracy: 90%+")
    
    # Group by severity
    by_severity = {}
    for query in system_output:
        sev = query['severity']
        by_severity[sev] = by_severity.get(sev, 0) + 1
    
    print(f"\n📊 Queries by Severity:")
    for severity, count in sorted(by_severity.items()):
        print(f"   {severity}: {count}")


if __name__ == "__main__":
    print("="*80)
    print("🧪 FORENSIC ARCHITECTURE - COMPREHENSIVE TEST SUITE")
    print("="*80)
    
    # Run all tests
    test1_results = test_with_sample_text()
    test2_results = test_with_actual_pdf()
    test_specific_patterns()
    compare_with_expected()
    
    print("\n" + "="*80)
    print("✅ TEST SUITE COMPLETE")
    print("="*80)
    
    # Summary
    print(f"\n📋 Summary:")
    print(f"   Test 1 (Sample): {len(test1_results) if test1_results else 0} queries")
    print(f"   Test 2 (PDF): {len(test2_results) if test2_results else 0} queries")
    print(f"   Test 3 (Patterns): See results above")
    print(f"   Test 4 (Accuracy): Manual review required")
    
    print(f"\n🎯 Next Steps:")
    print(f"   1. Review forensic_test_output.json")
    print(f"   2. If accuracy < 90%, tune patterns in checklists.py")
    print(f"   3. If accuracy >= 90%, integrate into main system")
    print(f"   4. See INTEGRATION_GUIDE.md for full integration")