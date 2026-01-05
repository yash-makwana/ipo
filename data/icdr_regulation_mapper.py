# data/icdr_regulation_mapper.py
"""
ICDR Regulation Reference Mapper
Maps NSE issue IDs to specific ICDR/Companies Act regulations
"""

ICDR_REGULATION_MAP = {
    # ===== GENERAL DISCLOSURE STANDARDS =====
    "MEASUREMENT_UNIT_CONSISTENCY": "ICDR Regulations - General Disclosure Standards",
    "UNDEFINED_JARGON": "ICDR Regulations - General Disclosure Standards",
    "SUPERLATIVE_EVIDENCE": "ICDR Regulations, Schedule VI - Forward-Looking Statements",
    "FORWARD_LOOKING_STATEMENTS": "ICDR Regulations, Schedule VI - Forward-Looking Statements",
    
    # ===== FINANCIAL INFORMATION =====
    "GEOGRAPHIC_REVENUE_SPLIT": "ICDR Regulations - Disclosure Requirements for Financial Information",
    "DOMESTIC_EXPORT_RECON": "ICDR Regulations - Disclosure Requirements for Financial Information",
    "REVENUE_MODEL_EXPLANATION": "ICDR Regulations - Disclosure Requirements for Financial Information",
    "PRODUCT_WISE_REVENUE_TABLE": "ICDR Regulations - Disclosure Requirements for Financial Information",
    "SKU_RECONCILIATION": "ICDR Regulations - Disclosure Requirements for Financial Information",
    "REVENUE_CHANNEL_BIFURCATION": "ICDR Regulations - Disclosure Requirements for Financial Information",
    "INDUSTRY_REVENUE_BIFURCATION": "ICDR Regulations - Disclosure Requirements for Financial Information",
    "PRODUCT_TREND_DECLINE": "ICDR Regulations - Disclosure Requirements for Financial Information",
    "REVENUE_PRODUCT_MISMATCH": "ICDR Regulations - Disclosure Requirements for Financial Information",
    
    # ===== BUSINESS OVERVIEW =====
    "DISTRIBUTOR_HEALTH_DETAIL": "ICDR Regulations - General Disclosure Standards",
    "SUPPLIER_CONCENTRATION": "ICDR Regulations - General Disclosure Standards",
    "CUSTOMER_DEPENDENCY_CONCENTRATION": "ICDR Regulations - General Disclosure Standards",
    "TOP_10_CLIENTS_RP": "ICDR Regulations - General Disclosure Standards",
    "DISTRIBUTION_NETWORK": "ICDR Regulations - General Disclosure Standards",
    "EXCLUSIVE_DISTRIBUTOR_VERIFICATION": "ICDR Regulations - General Disclosure Standards",
    "CHINESE_DISTRIBUTOR_IDENTIFICATION": "ICDR Regulations - General Disclosure Standards",
    
    # ===== HUMAN RESOURCES =====
    "ATTRITION_RATE": "ICDR Regulations - General Disclosure Standards",
    "MANAGEMENT_EXPERIENCE_INDIVIDUAL": "Regulation 403(b), 403(c)",
    "MANAGEMENT_EXPERIENCE_JARGON": "ICDR Regulations - General Disclosure Standards",
    "KEY_MAN_DEPENDENCY_RISK": "ICDR Regulations - Disclosure Requirements for Risk Factors",
    
    # ===== OPERATIONS & MANUFACTURING =====
    "CAPACITY_CERTIFICATION": "ICDR Regulations - General Disclosure Standards",
    "CAPACITY_UTILIZATION": "ICDR Regulations - General Disclosure Standards",
    "OWN_VS_CONTRACTUAL_MANUFACTURING": "ICDR Regulations - General Disclosure Standards",
    "OPERATIONAL_SCRAP": "ICDR Regulations - General Disclosure Standards",
    "PROCESS_FLOW_ALIGNMENT": "ICDR Regulations - General Disclosure Standards",
    "PROCESS_LABEL_CONTRADICTION": "ICDR Regulations - General Disclosure Standards",
    "UTILITIES_POWER_WATER": "ICDR Regulations - General Disclosure Standards",
    
    # ===== R&D AND INNOVATION =====
    "RD_INVESTMENT_DISCLOSURE": "ICDR Regulations - General Disclosure Standards",
    "BRANDING_INVESTMENT_QUANTIFICATION": "ICDR Regulations - General Disclosure Standards",
    "PRODUCT_USAGE_NVAH": "ICDR Regulations - General Disclosure Standards",
    
    # ===== QUALITY & CERTIFICATIONS =====
    "QA_INSPECTION_CERT_PROCESS": "ICDR Regulations - General Disclosure Standards",
    "ISO_CERTIFICATIONS": "[AIBI Compendium, Section: Complete Text]",
    "BIS_CERTIFICATION": "ICDR Regulations - General Disclosure Standards",
    
    # ===== PROCUREMENT & SUPPLY CHAIN =====
    "RAW_MATERIAL_PRICE_VOLATILITY": "ICDR Regulations - Disclosure Requirements for Risk Factors",
    "PROCUREMENT_GEOGRAPHY_FLUCTUATION": "ICDR Regulations - General Disclosure Standards",
    "COUNTRY_WISE_IMPORT_TABLE": "ICDR Regulations - General Disclosure Standards",
    "STATE_WISE_DOMESTIC_DEPENDENCY": "ICDR Regulations - General Disclosure Standards",
    "LOGISTICS_MECHANISM_AUDIT": "ICDR Regulations - General Disclosure Standards",
    
    # ===== COMPLIANCE & LEGAL =====
    "CSR_BUDGET_EXECUTION": "ICDR Regulations - General Disclosure Requirements",
    "EPF_ESIC_COMPLIANCE_NON_PAYMENT": "ICDR Regulations - General Disclosure Standards",
    "EHS_VIOLATIONS_RISK": "ICDR Regulations - Disclosure Requirements for Risk Factors",
    "REGULATORY_ACTIONS_HISTORY": "ICDR Regulations - General Disclosure Standards",
    "LITIGATION_COMPLIANCE_STATUS": "ICDR Regulations - General Disclosure Standards",
    "FACTORY_LICENSE_CLEARANCE_GAP": "ICDR Regulations - General Disclosure Standards",
    "GOVERNMENT_APPROVALS": "[AIBI Compendium, Section: Complete Text]",
    "GST_CERTIFICATES": "[AIBI Compendium, Section: Complete Text]",
    "SHOPS_ESTABLISHMENT_REGISTRATION": "[AIBI Compendium, Section: Complete Text]",
    
    # ===== ASSETS & PROPERTIES =====
    "LEASE_STATUS_MANDATORY": "ICDR Regulations - General Disclosure Requirements",
    "LEASE_EXPIRY_RISK": "ICDR Regulations - Disclosure Requirements for Risk Factors",
    "AGREEMENT_TO_SELL_LAND": "ICDR Regulations - General Disclosure Standards",
    "FIXED_ASSET_PHYSICAL_VERIFICATION": "ICDR Regulations - General Disclosure Standards",
    "PPE_SURGE_RATIONALE": "ICDR Regulations - Disclosure Requirements for Financial Information",
    
    # ===== RELATED PARTY TRANSACTIONS =====
    "ARM_LENGTH_RPT_DISCLOSURE": "ICDR Regulations - Disclosure Requirements for Related Party Transactions",
    "ARMS_LENGTH_RPT_DISCLOSURE": "ICDR Regulations - Disclosure Requirements for Related Party Transactions",
    "RPT_LOANS_ADVANCES": "ICDR Regulations - Disclosure Requirements for Related Party Transactions",
    
    # ===== FINANCIAL METRICS =====
    "INSURANCE_AUDIT_MISMATCH": "ICDR Regulations - General Disclosure Requirements",
    "WORKING_CAPITAL_INTENSITY_RATIONALE": "ICDR Regulations - Disclosure Requirements for Financial Information",
    "RECEIVABLES_SURGE_RISK": "ICDR Regulations - Disclosure Requirements for Risk Factors",
    "PAT_MARGIN_PEER_BENCHMARK": "ICDR Regulations - General Disclosure Standards",
    "KPI_PEER_COMPARISON_RISK": "ICDR Regulations - Disclosure Requirements for Risk Factors",
    "CONTINGENT_LIABILITIES_GUARANTEES": "ICDR Regulations - Disclosure Requirements for Financial Information",
    
    # ===== GOVERNANCE =====
    "SUBSIDIARY_RATIONALE": "ICDR Regulations - General Disclosure Standards",
    "AUDITOR_RELIANCE_NAMES": "ICDR Regulations - General Disclosure Standards",
    "AUDITOR_CHANGE_5YR": "ICDR Regulations - General Disclosure Standards",
    "FINANCIAL_CERTIFICATION_MD": "ICDR Regulations - General Disclosure Standards",
    
    # ===== OBJECTS OF THE ISSUE =====
    "OBJECTS_OF_ISSUE_UTILISATION": "ICDR Regulations - Disclosure Requirements for Objects of the Issue",
    "EXPANSION_EXECUTION_STEPS": "ICDR Regulations - Disclosure Requirements for Objects of the Issue",
    "CUSTOM_MACHINERY_INTERNATIONAL": "ICDR Regulations - General Disclosure Standards",
    
    # ===== RISK FACTORS =====
    "ORDER_BOOK_AUTHENTICITY": "ICDR Regulations - General Disclosure Standards",
    "DEPENDENCY_ON_GOVERNMENT_POLICIES": "ICDR Regulations - Disclosure Requirements for Risk Factors",
    "CUSTOMER_CHURN_REPEAT": "ICDR Regulations - General Disclosure Standards",
    
    # ===== TECHNICAL & PRODUCT =====
    "PRODUCT_TECHNICAL_SEPARATION": "ICDR Regulations - General Disclosure Standards",
    "TRADEMARK_COVERAGE_GAP": "ICDR Regulations - General Disclosure Standards",
    "BRAND_OWNERSHIP": "[AIBI Compendium, Section: Complete Text]",
    
    # ===== DATA & FORMATTING =====
    "IT_SECURITY_CONTRADICTION": "ICDR Regulations - General Disclosure Standards",
    "DATA_BACKUP_DISASTER_RECOVERY": "[AIBI Compendium, Section: Complete Text]",
    "REPETITIVE_TABLE_REMOVAL": "ICDR Regulations - General Disclosure Standards",
    
    # ===== CROSS-PAGE CONSISTENCY =====
    "ENTITY_DESCRIPTION_CONTRADICTION": "ICDR Regulations - General Disclosure Standards",
    "CROSS_PAGE_INCONSISTENCY": "ICDR Regulations - General Disclosure Standards",
}

# Severity to regulation category mapping
SEVERITY_REGULATION_MAP = {
    "Critical - Valuation": "ICDR Regulations - Disclosure Requirements for Financial Information",
    "Critical - Legal": "ICDR Regulations - General Disclosure Standards",
    "Critical - Operational": "ICDR Regulations - General Disclosure Standards",
    "Material": "ICDR Regulations - General Disclosure Standards",
    "Observation": "ICDR Regulations - General Disclosure Standards",
    "Clarification": "ICDR Regulations - General Disclosure Standards",
}

def get_regulation_reference(issue_id: str, severity: str = None) -> str:
    """
    Get ICDR regulation reference for a given issue ID
    
    Args:
        issue_id: The NSE issue identifier
        severity: Optional severity level for fallback
        
    Returns:
        ICDR regulation reference string
    """
    # Try exact match first
    if issue_id in ICDR_REGULATION_MAP:
        return ICDR_REGULATION_MAP[issue_id]
    
    # Fallback to severity-based mapping
    if severity and severity in SEVERITY_REGULATION_MAP:
        return SEVERITY_REGULATION_MAP[severity]
    
    # Ultimate fallback
    return "ICDR Regulations - General Disclosure Standards"


def add_regulation_to_query(query_dict: dict, issue_id: str) -> dict:
    """
    Add regulation reference to a query dictionary
    
    Args:
        query_dict: Query dictionary with 'text', 'page', etc.
        issue_id: The NSE issue identifier
        
    Returns:
        Enhanced query dictionary with regulation_ref
    """
    severity = query_dict.get('severity', query_dict.get('type', ''))
    regulation_ref = get_regulation_reference(issue_id, severity)
    
    query_dict['regulation_ref'] = regulation_ref
    return query_dict
