from typing import List, Dict, Any


def format_nse_queries_for_output(queries: List[Dict[str, Any]]) -> str:
    """
    Format NSE queries to match actual NSE letter format
    
    Args:
        queries: List of query dicts with:
            - page: page number
            - observation: query text
            - severity: Major/Minor/Critical/Observation
            - regulation_ref: ICDR reference
            - category: optional category name
            
    Returns:
        Formatted string matching NSE letter style
    """
    
    if not queries:
        return "No material observations were identified."
    
    # Sort by page number (handle ranges like "145 to 147")
    def extract_first_page(page_str):
        """Extract first page number from string like '145' or '145 to 147'"""
        if isinstance(page_str, int):
            return page_str
        if isinstance(page_str, str):
            # Handle "General", "Various", etc.
            if not page_str[0].isdigit():
                return 9999  # Put at end
            # Extract first number
            import re
            match = re.search(r'\d+', str(page_str))
            if match:
                return int(match.group())
        return 9999
    
    sorted_queries = sorted(queries, key=lambda q: extract_first_page(q.get('page', 9999)))
    
    output_lines = []
    
    for query in sorted_queries:
        page = query.get('page', '—')
        observation = query.get('observation', query.get('text', ''))
        severity = query.get('severity', 'Minor')
        regulation_ref = query.get('regulation_ref', 'ICDR Regulations - General Disclosure Standards')
        category = query.get('category', '')
        
        # ===== FORMAT MATCHING PDF EXACTLY =====
        
        # Title (if category provided)
        if category:
            output_lines.append(category)
        
        # Observation text (should already start with "On page no. X" or "Kindly...")
        output_lines.append(observation)
        
        # Extract recommendation if it's in the observation
        # NSE observations often have two parts:
        # 1. The issue description
        # 2. "Recommendation: Kindly..."
        if "Recommendation:" in observation or "Kindly" in observation:
            # Already formatted properly
            pass
        else:
            # Add recommendation line
            if "provide" in observation.lower() or "disclose" in observation.lower():
                output_lines.append(f"Recommendation: {observation}")
        
        # Regulation reference
        output_lines.append(f"Regulation Ref: {regulation_ref}")
        
        # Severity + Page (on same line at end)
        output_lines.append(f"{severity}Page {page}")
        
        # Blank line between queries
        output_lines.append("")
    
    return "\n".join(output_lines)


def format_nse_letter_style(
    queries: List[Dict[str, Any]],
    chapter_name: str = "Business Overview",
    company_name: str = "the Company"
) -> str:
    """
    Format queries as a complete NSE letter
    
    This matches the style from the uploaded PDF with proper structure
    """
    
    if not queries:
        return f"No material observations were identified in the {chapter_name} chapter."
    
    # Group queries by category for better organization
    categorized = {}
    uncategorized = []
    
    for q in queries:
        cat = q.get('category', '')
        if cat:
            if cat not in categorized:
                categorized[cat] = []
            categorized[cat].append(q)
        else:
            uncategorized.append(q)
    
    output_lines = []
    output_lines.append(f"{chapter_name} - NSE Queries")
    output_lines.append("=" * 80)
    output_lines.append("")
    
    # Output categorized queries
    for category, cat_queries in categorized.items():
        formatted = format_nse_queries_for_output(cat_queries)
        output_lines.append(formatted)
    
    # Output uncategorized queries
    if uncategorized:
        formatted = format_nse_queries_for_output(uncategorized)
        output_lines.append(formatted)
    
    return "\n".join(output_lines)


def format_for_api_response(queries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Format queries for JSON API response
    
    Returns list of properly structured query objects
    """
    
    formatted_queries = []
    
    for query in queries:
        formatted_queries.append({
            'page': str(query.get('page', '—')),
            'observation': query.get('observation', query.get('text', '')),
            'severity': query.get('severity', 'Minor'),
            'category': query.get('category', 'General'),
            'regulation_ref': query.get('regulation_ref', 'ICDR Regulations - General Disclosure Standards'),
            'issue_id': query.get('issue_id', ''),
            'missing_elements': query.get('missing_elements', []),
        })
    
    return formatted_queries


# ===== BACKWARD COMPATIBILITY =====

def format_nse_output(queries: List[Dict]) -> str:
    """
    Backward compatible with SystemA's nse_output_formatter.py
    
    This is called by multi_agent_orchestrator.py
    """
    return format_nse_queries_for_output(queries)


def format_nse_section(title: str, queries: List[Dict]) -> str:
    """Backward compatible section formatter"""
    return format_nse_letter_style(queries, chapter_name=title)
