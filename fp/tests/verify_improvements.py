
import unittest
from typing import Dict, Any
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from context_aware_query_generators import ContextAwareQueryGenerator
from regulation_citation_mapper import RegulationCitationMapper, get_regulation_mapper
from advanced_intelligence_layers import DraftingHygieneScanner

class TestSystemImprovements(unittest.TestCase):
    
    def setUp(self):
        self.query_gen = ContextAwareQueryGenerator()
        self.reg_mapper = get_regulation_mapper()
        self.hygiene_scanner = DraftingHygieneScanner()
        
    def test_finance_anomaly_revenue_profit_divergence(self):
        """Test detection of Revenue Growth vs PAT Decline"""
        print("\nTesting Financial Anomaly (Revenue Up, PAT Down)...")
        
        # Mock context with divergence
        context = {
            'trends': [
                {
                    'metric': 'revenue',
                    'cagr': 15.5, # > 10%
                    'pages': [10, 11]
                },
                {
                    'metric': 'pat',
                    'cagr': -5.2, # Declining
                    'pages': [10, 11]
                }
            ],
            'products': [],
            'segments': []
        }
        
        queries = self.query_gen.financial_generator._check_profit_growth_mismatch(context)
        
        self.assertTrue(len(queries) > 0)
        self.assertEqual(queries[0]['issue_id'], 'REVENUE_PAT_DIVERGENCE')
        print(f"✅ Detected Divergence: {queries[0]['observation'][:100]}...")

    def test_capacity_utilization_high(self):
        """Test detection of High Capacity Utilization without expansion"""
        print("\nTesting High Capacity Utilization...")
        
        context = {
            'capacity': [
                {
                    'unit': 'Unit 1',
                    'utilization_pct': 95.0,
                    'pages': [20]
                }
            ],
            'has_expansion_plans': False
        }
        
        queries = self.query_gen.operational_generator._check_capacity_utilization(context)
        
        self.assertTrue(len(queries) > 0)
        self.assertEqual(queries[0]['issue_id'], 'HIGH_CAPACITY_UTILIZATION')
        print(f"✅ Detected High Utilization: {queries[0]['observation'][:100]}...")

    def test_regulation_citation_specificity(self):
        """Test granular regulation mapping"""
        print("\nTesting Regulation Citation Specificity...")
        
        # Test 1: Board Composition (Should have ICDR + Companies Act)
        citation = self.reg_mapper.enhance_citation(None, "Composition of Board of Directors")
        print(f"   Citation for 'Board': {citation}")
        self.assertIn("Regulation 31", citation)
        self.assertIn("149", citation) # Companies Act cross-ref (Section or Sections)
        
        # Test 2: IPO Objects (Specific sub-reg)
        citation2 = self.reg_mapper.get_specific_citation("Objects of the Issue details", "ICDR")
        self.assertIn("Schedule VI Part A (2)", citation2)
        
    def test_drafting_hygiene_dates(self):
        """Test date consistency check"""
        print("\nTesting Date Consistency Hygiene...")
        
        # Provide > 2 of each to trigger threshold
        text = """
        Meeting 1: 31/03/2024
        Meeting 2: 30/06/2024
        Meeting 3: 30/09/2024
        
        Next: 15-Apr-2024
        Next: 15-May-2024
        Next: 15-Jun-2024
        """
        queries = self.hygiene_scanner._check_date_consistency(5, text)
        
        self.assertTrue(len(queries) > 0)
        self.assertEqual(queries[0]['issue_id'], 'INCONSISTENT_DATE_FORMAT')
        print(f"✅ Detected Date Inconsistency: {queries[0]['observation'][:100]}...")

    def test_statement_interrogation_vague(self):
        """Test vague statement interrogation"""
        print("\nTesting Vague Statement Interrogation...")
        
        # Make content > 20 chars
        pages_dict = {
            50: "We are a market leader in the high-performance engineering polymer segment of India."
        }
        
        queries = self.query_gen.statement_interrogator.generate_queries(pages_dict, {})
        
        self.assertTrue(len(queries) > 0)
        self.assertIn("market leader", queries[0]['observation'])
        print(f"✅ Detected Vague Claim: {queries[0]['observation'][:100]}...")

if __name__ == '__main__':
    unittest.main()
