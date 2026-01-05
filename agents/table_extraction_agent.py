"""
Table Extraction Agent
======================
Extracts tables from DRHP PDFs and verifies calculations
Supports:
- Table extraction using multiple libraries
- Numerical verification
- Formula checking
- Data consistency validation
"""

import time
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from pathlib import Path
import json
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv('.env-local')
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


class TableExtractionAgent:
    """
    Table Extraction and Verification Agent
    
    Responsibilities:
    1. Extract tables from PDF using multiple methods
    2. Parse table structure and data
    3. Verify calculations (sums, percentages, ratios)
    4. Check data consistency across tables
    5. Validate against legal requirements
    """
    
    def __init__(self):
        """Initialize Table Extraction Agent"""
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model_name = "gemini-2.0-flash-exp"
        print(f"✅ TableExtractionAgent initialized")
    
    def extract_tables_camelot(self, pdf_path: str) -> List[pd.DataFrame]:
        """
        Extract tables using Camelot (best for bordered tables)
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            List of pandas DataFrames
        """
        try:
            import camelot
            
            print(f"   📊 Extracting tables with Camelot...")
            tables = camelot.read_pdf(pdf_path, pages='all', flavor='lattice')
            
            dataframes = [table.df for table in tables]
            print(f"   ✅ Extracted {len(dataframes)} tables")
            return dataframes
            
        except ImportError:
            print(f"   ⚠️  Camelot not installed. Install with: pip install camelot-py[cv]")
            return []
        except Exception as e:
            print(f"   ⚠️  Camelot extraction failed: {e}")
            return []
    
    def extract_tables_tabula(self, pdf_path: str) -> List[pd.DataFrame]:
        """
        Extract tables using Tabula (best for stream tables)
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            List of pandas DataFrames
        """
        try:
            import tabula
            
            print(f"   📊 Extracting tables with Tabula...")
            tables = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True)
            
            print(f"   ✅ Extracted {len(tables)} tables")
            return tables
            
        except ImportError:
            print(f"   ⚠️  Tabula not installed. Install with: pip install tabula-py")
            return []
        except Exception as e:
            print(f"   ⚠️  Tabula extraction failed: {e}")
            return []
    
    def extract_all_tables(self, pdf_path: str) -> Dict[str, List[pd.DataFrame]]:
        """
        Extract tables using all available methods
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            Dictionary with extraction method as key and tables as value
        """
        print(f"\n{'='*60}")
        print(f"📊 TABLE EXTRACTION")
        print(f"{'='*60}")
        print(f"   File: {pdf_path}")
        
        results = {}
        
        # Try Camelot
        camelot_tables = self.extract_tables_camelot(pdf_path)
        if camelot_tables:
            results['camelot'] = camelot_tables
        
        # Try Tabula
        tabula_tables = self.extract_tables_tabula(pdf_path)
        if tabula_tables:
            results['tabula'] = tabula_tables
        
        total_tables = sum(len(tables) for tables in results.values())
        print(f"\n   ✅ Total tables extracted: {total_tables}")
        
        return results
    
    def verify_table_calculations(self, df: pd.DataFrame, table_context: str = "") -> Dict[str, Any]:
        """
        Verify calculations in a table (sums, percentages, totals)
        
        Args:
            df: Pandas DataFrame
            table_context: Context about what the table represents
        
        Returns:
            Verification results with errors found
        """
        print(f"\n   🔍 Verifying calculations...")
        
        errors = []
        warnings = []
        
        try:
            # Convert to numeric where possible
            df_numeric = df.apply(pd.to_numeric, errors='ignore')
            
            # Check 1: Look for "Total" rows and verify sums
            for idx, row in df_numeric.iterrows():
                row_label = str(df.iloc[idx, 0]).lower()
                
                if 'total' in row_label or 'sum' in row_label:
                    # Find numeric columns
                    numeric_cols = df_numeric.select_dtypes(include=[np.number]).columns
                    
                    for col in numeric_cols:
                        # Get values above this row in same column
                        values_above = df_numeric.loc[:idx-1, col].dropna()
                        
                        if len(values_above) > 0:
                            expected_sum = values_above.sum()
                            actual_value = df_numeric.loc[idx, col]
                            
                            if pd.notna(actual_value):
                                diff = abs(expected_sum - actual_value)
                                if diff > 0.01:  # Allow small rounding errors
                                    errors.append({
                                        'type': 'SUM_MISMATCH',
                                        'row': int(idx),
                                        'column': col,
                                        'expected': float(expected_sum),
                                        'actual': float(actual_value),
                                        'difference': float(diff)
                                    })
            
            # Check 2: Look for percentage columns and verify they sum to 100
            for col in df_numeric.select_dtypes(include=[np.number]).columns:
                col_name = str(col).lower()
                if '%' in col_name or 'percent' in col_name or 'pct' in col_name:
                    total = df_numeric[col].sum()
                    if abs(total - 100) > 1.0:  # Allow 1% tolerance
                        warnings.append({
                            'type': 'PERCENTAGE_SUM',
                            'column': col,
                            'expected': 100.0,
                            'actual': float(total),
                            'difference': float(abs(total - 100))
                        })
            
            # Check 3: Look for consistency across rows
            numeric_cols = df_numeric.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 2:
                # Check if any column is sum/difference of others
                for i, col1 in enumerate(numeric_cols):
                    for j, col2 in enumerate(numeric_cols[i+1:], i+1):
                        for k, col3 in enumerate(numeric_cols[j+1:], j+1):
                            # Check if col3 = col1 + col2
                            expected = df_numeric[col1] + df_numeric[col2]
                            actual = df_numeric[col3]
                            diff = (expected - actual).abs()
                            
                            if (diff < 0.01).all():  # All rows match
                                warnings.append({
                                    'type': 'FORMULA_DETECTED',
                                    'formula': f"{col3} = {col1} + {col2}",
                                    'verified': True
                                })
            
            print(f"   ✅ Found {len(errors)} errors, {len(warnings)} warnings")
            
            return {
                'errors': errors,
                'warnings': warnings,
                'total_checks': len(errors) + len(warnings),
                'status': 'FAILED' if errors else 'PASSED'
            }
            
        except Exception as e:
            print(f"   ⚠️  Verification error: {e}")
            return {
                'errors': [{'type': 'VERIFICATION_ERROR', 'message': str(e)}],
                'warnings': [],
                'status': 'ERROR'
            }
    
    def analyze_table_with_llm(
        self, 
        df: pd.DataFrame, 
        obligation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Use LLM to analyze if table satisfies an obligation
        
        Args:
            df: Table as DataFrame
            obligation: Legal obligation to check
        
        Returns:
            Analysis results
        """
        # Convert table to readable format
        table_str = df.to_string(index=False, max_rows=20)
        
        prompt = f"""You are a financial compliance expert.

LEGAL OBLIGATION:
{obligation.get('requirement_text', 'Check table compliance')}

TABLE DATA:
{table_str}

TASK: Analyze if this table satisfies the legal obligation.

Check for:
1. Required columns present
2. Required time periods (e.g., last 3 FYs)
3. Calculations are correct
4. All mandatory disclosures present

Respond with ONLY JSON:
{{
  "status": "COMPLIANT|NON_COMPLIANT|PARTIAL",
  "explanation": "What's present or missing",
  "missing_items": ["list of missing required items"],
  "calculation_errors": ["any calculation errors found"],
  "confidence": 0.0-1.0
}}
"""
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=1500,
                )
            )
            
            text = response.text.strip()
            
            # Clean JSON
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0]
            elif '```' in text:
                text = text.split('```')[1].split('```')[0]
            
            result = json.loads(text.strip())
            return result
            
        except Exception as e:
            print(f"   ⚠️  LLM analysis error: {e}")
            return {
                'status': 'ERROR',
                'explanation': str(e),
                'confidence': 0.0
            }
    
    def process_document_tables(
        self, 
        pdf_path: str,
        obligations: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Complete table processing pipeline
        
        Args:
            pdf_path: Path to PDF
            obligations: Optional list of obligations to check
        
        Returns:
            Complete table analysis results
        """
        start_time = time.time()
        
        # Extract tables
        extracted_tables = self.extract_all_tables(pdf_path)
        
        if not extracted_tables:
            return {
                'status': 'NO_TABLES_FOUND',
                'message': 'No tables could be extracted from document'
            }
        
        # Process each table
        all_results = []
        
        for method, tables in extracted_tables.items():
            for i, df in enumerate(tables):
                print(f"\n{'='*60}")
                print(f"📊 TABLE {i+1} ({method})")
                print(f"{'='*60}")
                print(f"   Shape: {df.shape[0]} rows × {df.shape[1]} columns")
                
                # Verify calculations
                calc_results = self.verify_table_calculations(df)
                
                # If obligations provided, check compliance
                obligation_results = []
                if obligations:
                    for obligation in obligations:
                        result = self.analyze_table_with_llm(df, obligation)
                        obligation_results.append(result)
                
                all_results.append({
                    'table_index': i + 1,
                    'extraction_method': method,
                    'shape': {'rows': int(df.shape[0]), 'columns': int(df.shape[1])},
                    'calculation_verification': calc_results,
                    'obligation_compliance': obligation_results,
                    'table_preview': df.head(5).to_dict()
                })
        
        elapsed_time = time.time() - start_time
        
        return {
            'status': 'SUCCESS',
            'total_tables': len(all_results),
            'tables': all_results,
            'processing_time_seconds': elapsed_time
        }


def get_table_extraction_agent():
    """Factory function to get table extraction agent"""
    return TableExtractionAgent()


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("="*80)
    print("🧪 TESTING TABLE EXTRACTION AGENT")
    print("="*80)
    
    # Create sample table for testing
    sample_data = {
        'Year': ['2021', '2022', '2023', 'Total'],
        'Revenue': [100, 150, 200, 450],
        'Expenses': [80, 120, 160, 360],
        'Profit': [20, 30, 40, 90]
    }
    df = pd.DataFrame(sample_data)
    
    print("\n📊 Sample Table:")
    print(df)
    
    # Test calculation verification
    agent = get_table_extraction_agent()
    results = agent.verify_table_calculations(df)
    
    print(f"\n{'='*60}")
    print(f"VERIFICATION RESULTS")
    print(f"{'='*60}")
    print(f"Status: {results['status']}")
    print(f"Errors: {len(results['errors'])}")
    print(f"Warnings: {len(results['warnings'])}")
    
    if results['errors']:
        print("\nErrors found:")
        for error in results['errors']:
            print(f"  - {error}")
    
    print("\n✅ Table Extraction Agent Test Complete!")