"""
Enhanced Compliance Output Formatter
Generates detailed, officer-style compliance reports
"""

def generate_detailed_compliance_output(requirement, verification_result, document_context):
    """
    Generate detailed compliance output similar to SEBI officer's format
    
    Args:
        requirement: dict with requirement details
        verification_result: dict with AI verification results
        document_context: dict with document metadata
    """
    
    # 1. REQUIREMENT HEADER (Expanded)
    output = f"""
{'='*80}
REQUIREMENT ANALYSIS
{'='*80}

Requirement ID: {requirement['id']}
Full Text: {requirement['requirement_text']}

"""
    
    # 2. STATUS (Clear and Prominent)
    status = verification_result['status']
    status_emoji = {
        'PRESENT': '✅',
        'MISSING': '❌', 
        'VIOLATED': '⚠️',
        'UNCLEAR': '❓'
    }
    
    output += f"""
Status: {status_emoji[status]} {status}

"""
    
    # 3. REGULATION REFERENCE (Detailed)
    output += f"""
Regulation Reference:
- Act/Regulation: {requirement['regulation']} 
- Chapter: {requirement['chapter_title']} (Chapter {requirement['chapter_number']})
- Section: {requirement['section_number']} - {requirement['section_title']}
- Applicability: {requirement.get('applies_to', 'All issuers')}
- Mandatory: {'Yes' if requirement['mandatory'] else 'No'}
- Category: {requirement['category']}

"""
    
    # 4. COMPLIANCE DETAILS (Why status was assigned)
    if status == 'PRESENT':
        output += f"""
Compliance Details:
✅ Requirement is adequately addressed in the document.

Evidence Found:
{verification_result.get('evidence', 'No specific evidence extracted')}

Location in Document:
- Pages: {', '.join(map(str, verification_result.get('drhp_pages', ['Not specified'])))}
- Section: {document_context['section_name']}

Confidence Level: {verification_result.get('confidence', 0.5)*100:.0f}%

"""
    
    elif status == 'MISSING':
        output += f"""
Non-Compliance Details:
❌ The document does not contain evidence of this requirement.

What Was Expected:
{generate_expected_disclosure(requirement)}

What Was Found:
{verification_result.get('explanation', 'No relevant content found in document')}

Searched Sections:
- Document: {document_context['document_name']}
- Pages Analyzed: {document_context.get('pages_searched', 'All pages')}
- Section: {document_context['section_name']}

"""
    
    elif status == 'UNCLEAR':
        output += f"""
Unclear Compliance Status:
❓ Unable to determine if requirement is met due to insufficient information.

Reason for Uncertainty:
{verification_result.get('explanation', 'Document context insufficient for verification')}

Additional Information Needed:
{generate_clarification_needed(requirement)}

"""
    
    elif status == 'VIOLATED':
        output += f"""
Violation Details:
⚠️ Document contains information that contradicts this requirement.

Nature of Violation:
{verification_result.get('explanation', 'Regulatory requirement not met')}

Evidence of Violation:
{verification_result.get('evidence', 'See document analysis')}

"""
    
    # 5. EXPECTED DISCLOSURE (Where it should be)
    output += f"""
Expected Disclosure Location:
- Primary Chapter: {get_expected_chapter(requirement['category'])}
- Alternative Chapters: {get_alternative_chapters(requirement['category'])}
- Current Document: {document_context['document_name']}

"""
    
    # 6. IMPACT ASSESSMENT
    output += f"""
Impact on Issue:
{assess_impact(requirement, status)}

"""
    
    # 7. RECOMMENDATIONS
    output += f"""
Recommendations:
{generate_recommendations(requirement, status, document_context)}

"""
    
    # 8. TECHNICAL DETAILS
    output += f"""
{'='*80}
Technical Details
{'='*80}
Evidence Quality: {verification_result.get('evidence_quality', 'medium').upper()}
AI Confidence Score: {verification_result.get('confidence', 0.5):.2%}
Document Coverage: {document_context.get('coverage', 'Full document')}
Analysis Timestamp: {document_context.get('timestamp', 'Not recorded')}
{'='*80}

"""
    
    return output


def generate_expected_disclosure(requirement):
    """Generate what should have been disclosed"""
    category = requirement['category']
    
    templates = {
        'filing': """
- Date of filing with SEBI Board
- Acknowledgement/Receipt number from SEBI
- Fees paid as per Schedule III
- SEBI observations received date
- Status of compliance with observations
""",
        'financial': """
- Audited financial statements for last 3 years
- Restated financial statements with adjustments
- Peer review auditor certification
- Material accounting policies
""",
        'business': """
- Detailed description of business operations
- Manufacturing facilities and capacities
- Key products/services with specifications
- Market presence and competition
""",
        'management': """
- Complete profiles of directors and KMP
- Qualifications and experience details
- Remuneration structure and amounts
- Related party relationships
"""
    }
    
    return templates.get(category, "Detailed disclosure as per ICDR requirements")


def generate_clarification_needed(requirement):
    """What additional info is needed"""
    return f"""
1. Verify if disclosure exists in other chapters of the DRHP
2. Check annexures and appendices for supporting documents
3. Review material contracts section for related agreements
4. Consult with legal advisors on disclosure adequacy
5. Cross-reference with SEBI observation letter
"""


def get_expected_chapter(category):
    """Where this requirement should typically be disclosed"""
    mapping = {
        'filing': 'General Information / Regulatory Disclosures',
        'financial': 'Financial Information / Audited Financials',
        'business': 'Our Business / Industry Overview',
        'management': 'Our Management / Board of Directors',
        'risk': 'Risk Factors',
        'legal': 'Outstanding Litigations / Legal Proceedings'
    }
    return mapping.get(category, 'Refer to ICDR Schedule/Format')


def get_alternative_chapters(category):
    """Alternative places to look"""
    return "History and Corporate Matters, Material Contracts, Objects of the Issue"


def assess_impact(requirement, status):
    """Assess business impact of non-compliance"""
    if requirement['mandatory'] and status in ['MISSING', 'VIOLATED']:
        return """
❗ CRITICAL IMPACT
This is a mandatory requirement. Non-compliance may result in:
- SEBI rejecting the offer document
- Delay in obtaining final observations
- Need to refile corrected documents
- Potential penalties or regulatory action
- Issue opening timeline pushed back

Action Required: IMMEDIATE REMEDIATION BEFORE RHP FILING
"""
    elif status == 'UNCLEAR':
        return """
⚠️ MODERATE IMPACT  
Unclear compliance creates regulatory uncertainty:
- May trigger additional queries from SEBI
- Could delay observation issuance
- Requires clarification before proceeding

Action Required: CLARIFY AND PROVIDE ADDITIONAL DISCLOSURE
"""
    else:
        return """
✅ NO NEGATIVE IMPACT
Requirement appears to be adequately addressed.
"""


def generate_recommendations(requirement, status, document_context):
    """Generate actionable recommendations"""
    if status == 'MISSING':
        return f"""
1. IMMEDIATE ACTIONS:
   - Add disclosure in appropriate chapter (see Expected Location above)
   - Obtain supporting documents from internal teams
   - Draft disclosure text aligned with ICDR format
   
2. VERIFICATION STEPS:
   - Legal team to review disclosure completeness
   - Compliance team to cross-check against SEBI requirements
   - Merchant banker to validate disclosure adequacy
   
3. DOCUMENTATION:
   - Update draft RHP with required disclosure
   - Maintain working papers showing compliance
   - Prepare for potential SEBI queries on this topic

4. TIMELINE:
   - Complete disclosure addition within 2-3 business days
   - Include in next draft circulation to SEBI
"""
    elif status == 'UNCLEAR':
        return f"""
1. CLARIFICATION NEEDED:
   - Search other chapters: {get_alternative_chapters(requirement['category'])}
   - Check if partially disclosed elsewhere
   - Review materiality of this requirement
   
2. IF NOT FOUND ELSEWHERE:
   - Treat as MISSING and add disclosure
   - Follow recommendations for Missing status above

3. IF FOUND BUT INADEQUATE:
   - Enhance existing disclosure with more details
   - Cross-reference between chapters if needed
"""
    else:  # PRESENT or VIOLATED
        return f"""
1. MAINTAIN DOCUMENTATION:
   - Keep evidence of compliance readily accessible
   - Tag this section in RHP for easy reference
   
2. PERIODIC REVIEW:
   - Ensure disclosure remains accurate through offer period
   - Update if any material changes occur
"""


# Example Usage
if __name__ == "__main__":
    # Sample requirement
    requirement = {
        'id': 'ICDR_II_4_001',
        'requirement_text': 'File draft offer document with Board along with fees specified in Schedule III',
        'regulation': 'ICDR Regulations 2018',
        'chapter_number': 'II',
        'chapter_title': 'General Conditions for Public Issue',
        'section_number': '4',
        'section_title': 'Pre-issue filing requirements',
        'mandatory': True,
        'category': 'filing',
        'applies_to': 'All issuers'
    }
    
    # Sample verification result
    verification = {
        'status': 'MISSING',
        'confidence': 0.85,
        'explanation': 'No mention of SEBI filing or Schedule III fees in Our Business chapter',
        'evidence': '',
        'evidence_quality': 'high',
        'drhp_pages': []
    }
    
    # Sample document context
    context = {
        'document_name': 'Our Business (Chapter V)',
        'section_name': 'Business Overview',
        'pages_searched': '109-140',
        'coverage': 'Full chapter',
        'timestamp': '2025-12-06 14:30:00'
    }
    
    # Generate detailed output
    detailed_report = generate_detailed_compliance_output(
        requirement, verification, context
    )
    
    print(detailed_report)