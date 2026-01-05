"""
YoY Decline Detector - FIXES MISS #1
=====================================
Detects Year-over-Year declines in revenue, margins, volumes
and generates NSE-style queries for explanation.

This fixes the "Converted foam revenue decline" type misses.

Author: IPO Compliance System - Accuracy Enhancement
Date: January 2026
"""

import re
from typing import Dict, List, Tuple, Optional


class YoYDeclineDetector:
    """
    Detects YoY declines and generates NSE queries
    
    Catches patterns like:
    - Revenue dropped from ₹100 Cr (FY24) to ₹80 Cr (FY25)
    - Margin decreased from 15% to 12%
    - Volume fell from 1000 tons to 800 tons
    """
    
    def __init__(self):
        """Initialize decline detector"""
        
        # Metrics to track
        self.metrics = {
            'revenue': ['revenue', 'sales', 'turnover', 'income', 'topline'],
            'margin': ['margin', 'ebitda', 'profit margin', 'gross margin', 'operating margin'],
            'volume': ['volume', 'quantity', 'units', 'production', 'output'],
            'capacity': ['capacity utilization', 'plant capacity', 'utilization'],
            'profit': ['profit after tax', 'pat', 'net profit', 'bottomline', 'profit for the year'],
            'cashflow': ['cash flow from operations', 'operating cash flow', 'cash from operating activities']
        }
        
        # Decline threshold (10% drop triggers query for critical items, 15% others)
        self.decline_threshold = 0.10  # 10%

        
        print("✅ YoY Decline Detector initialized")
    
    def detect_declines(self, pages_dict: Dict[int, str]) -> List[Dict]:
        """
        Scan document for YoY declines
        
        Args:
            pages_dict: {page_num: page_text}
        
        Returns:
            List of decline queries
        """
        
        queries = []
        
        for page_num, text in pages_dict.items():
            
            # Find all financial comparisons
            comparisons = self._extract_comparisons(text)
            
            for comp in comparisons:
                
                # Check if significant decline
                if self._is_significant_decline(comp):
                    
                    query = self._generate_decline_query(comp, page_num)
                    queries.append(query)
        
        return queries
    
    def _extract_comparisons(self, text: str) -> List[Dict]:
        """
        Extract financial comparisons from text
        
        Returns:
            [
                {
                    'metric': 'revenue',
                    'item': 'converted foam',
                    'fy_prev': 'FY24',
                    'value_prev': 100.0,
                    'fy_curr': 'FY25', 
                    'value_curr': 80.0,
                    'unit': 'crore',
                    'context': 'Revenue from converted foam...'
                }
            ]
        """
        
        comparisons = []
        
        # Pattern 1: "X from ₹100 Cr (FY24) to ₹80 Cr (FY25)" or "X decreased by 20% from ₹100..."
        pattern1 = r'([\w\s]{3,30})\s+(?:from|declined|decreased|dropped|fell|reduced)\s+(?:from\s+)?(?:₹|Rs\.?)\s*([\d,]+(?:\.\d+)?)\s*([a-z.]+)?\s*(?:\(?(FY\d{2}|\d{4})\)?)\s+to\s+(?:₹|Rs\.?)\s*([\d,]+(?:\.\d+)?)\s*([a-z.]+)?\s*(?:\(?(FY\d{2}|\d{4})\)?)'
        
        for match in re.finditer(pattern1, text, re.IGNORECASE):
            metric_name = match.group(1).lower().strip()
            val_prev_str = match.group(2).replace(',', '')
            value_prev = float(val_prev_str)
            unit_prev = match.group(3) or 'crore'
            fy_prev = match.group(4)
            val_curr_str = match.group(5).replace(',', '')
            value_curr = float(val_curr_str)
            unit_curr = match.group(6) or 'crore'
            fy_curr = match.group(7)
            
            # Determine metric type
            metric_type = self._identify_metric(metric_name)
            
            if metric_type:
                comparisons.append({
                    'metric': metric_type,
                    'item': metric_name,
                    'fy_prev': fy_prev,
                    'value_prev': value_prev,
                    'fy_curr': fy_curr,
                    'value_curr': value_curr,
                    'unit': unit_prev,
                    'context': match.group(0)
                })
        
        # Pattern 2: Table/List format (FY24: ₹100, FY25: ₹80)
        # Improved regex for multi-year sequences
        pattern2 = r'(FY\d{2}|\d{4})\s*[:\-]?\s*(?:₹|Rs\.?)?\s*([\d,]+(?:\.\d+)?)\s*(?:cr|crore|lakh|million)?.*?[\s\n]+(FY\d{2}|\d{4})\s*[:\-]?\s*(?:₹|Rs\.?)?\s*([\d,]+(?:\.\d+)?)\s*(?:cr|crore|lakh|million)?'
        
        for match in re.finditer(pattern2, text, re.IGNORECASE | re.DOTALL):
            try:
                fy_prev = match.group(1)
                val_prev_str = match.group(2).replace(',', '').strip()
                if not val_prev_str: continue
                value_prev = float(val_prev_str)
                
                fy_curr = match.group(3)
                val_curr_str = match.group(4).replace(',', '').strip()
                if not val_curr_str: continue
                value_curr = float(val_curr_str)
            except ValueError:
                continue
            
            # Context window around the match
            start = max(0, match.start() - 150)
            context = text[start:match.end()]
            
            metric_type = self._identify_metric(context)
            
            if metric_type and value_prev > value_curr:
                comparisons.append({
                    'metric': metric_type,
                    'item': metric_type.capitalize(),
                    'fy_prev': fy_prev,
                    'value_prev': value_prev,
                    'fy_curr': fy_curr,
                    'value_curr': value_curr,
                    'unit': 'crore',
                    'context': f"...{text[match.start():match.end()]}"
                })
        
        return comparisons
        
        return comparisons
    
    def _identify_metric(self, text: str) -> Optional[str]:
        """Identify metric type from text"""
        
        text_lower = text.lower()
        
        for metric_type, keywords in self.metrics.items():
            if any(kw in text_lower for kw in keywords):
                return metric_type
        
        return None
    
    def _is_significant_decline(self, comparison: Dict) -> bool:
        """
        Check if decline is significant (>15%)
        
        Args:
            comparison: Comparison dict
        
        Returns:
            True if decline > threshold
        """
        
        value_prev = comparison['value_prev']
        value_curr = comparison['value_curr']
        
        if value_prev == 0:
            return False
        
        decline_pct = (value_prev - value_curr) / value_prev
        
        return decline_pct > self.decline_threshold
    
    def _generate_decline_query(self, comp: Dict, page_num: int) -> Dict:
        """Generate NSE-style query for decline"""
        
        value_prev = comp['value_prev']
        value_curr = comp['value_curr']
        decline_pct = ((value_prev - value_curr) / value_prev) * 100
        
        query_text = (
            f"It has been observed that {comp['item']} declined substantially "
            f"from ₹{value_prev} {comp['unit']} in {comp['fy_prev']} to "
            f"₹{value_curr} {comp['unit']} in {comp['fy_curr']} "
            f"(a decline of {decline_pct:.1f}%). "
            f"Provide detailed reasons for the decline and confirm the impact "
            f"on future operations. Provide revised draft along with confirmation "
            f"that the same shall be updated in the prospectus."
        )
        
        return {
            'page': str(page_num),
            'text': query_text,
            'type': 'TYPE_YOY_DECLINE',
            'issue_id': 'YOY_REVENUE_DECLINE',
            'severity': 'Critical',
            'category': 'Financial'
        }


def get_yoy_decline_detector():
    """Factory function"""
    return YoYDeclineDetector()


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """Test the detector"""
    
    detector = YoYDeclineDetector()
    
    # Test text
    test_text = """
    Revenue from converted foam products declined from ₹120 crore in FY24 
    to ₹95 crore in FY25 due to market conditions.
    
    EBITDA margin decreased from 18% (FY24) to 14% (FY25).
    
    Financial Performance:
    FY24: ₹500 crore
    FY25: ₹420 crore
    """
    
    pages_dict = {47: test_text}
    
    queries = detector.detect_declines(pages_dict)
    
    print(f"\n🔍 Found {len(queries)} decline queries:")
    for q in queries:
        print(f"\n{q['text']}")