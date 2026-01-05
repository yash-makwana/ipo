# data/checklists.py

"""
V12: DATA LAYER - NSE ISSUE REGISTRY (FORENSIC AUDIT)
- Habit 1: Definition Policing (Jargon/Acronyms)
- Habit 2: Unit Consistency (Measurement Audit)
- Habit 3: Asset & Lease Risk (RPT/Registration)
- Habit 4: SKU & Product Taxonomy
- Habit 5: Sales Channel & Supplier Depth
"""

BUSINESS_OVERVIEW_CHECKLIST = [
    "REVENUE_MODEL_EXPLANATION",
    "PRODUCT_WISE_REVENUE_TABLE",
    "SKU_RECONCILIATION",
    "REVENUE_CHANNEL_BIFURCATION",
    "DISTRIBUTOR_HEALTH_DETAIL",
    "GEOGRAPHIC_REVENUE_SPLIT",
    "DOMESTIC_EXPORT_RECON",
    "SUPPLIER_CONCENTRATION",
    "RD_INVESTMENT_DISCLOSURE",
    "ATTRITION_RATE",
    "CAPACITY_CERTIFICATION",
    "INSURANCE_AUDIT_MISMATCH",
    "CSR_BUDGET_EXECUTION",
    "LEASE_STATUS_MANDATORY",
    "SUBSIDIARY_RATIONALE",
    "UNDEFINED_JARGON",
    "MEASUREMENT_UNIT_CONSISTENCY",
    "SUPERLATIVE_EVIDENCE"
]

MANDATORY_BUSINESS_OVERVIEW = [
    "REVENUE_MODEL_EXPLANATION",
    "PRODUCT_WISE_REVENUE_TABLE",
    "SKU_RECONCILIATION",
    "REVENUE_CHANNEL_BIFURCATION",
    "DISTRIBUTOR_HEALTH_DETAIL",
    "GEOGRAPHIC_REVENUE_SPLIT",
    "DOMESTIC_EXPORT_RECON",
    "SUPPLIER_CONCENTRATION",
    "RD_INVESTMENT_DISCLOSURE",
    "ATTRITION_RATE",
    "CAPACITY_CERTIFICATION",
    "INSURANCE_AUDIT_MISMATCH",
    "CSR_BUDGET_EXECUTION",
    "LEASE_STATUS_MANDATORY",
    "SUBSIDIARY_RATIONALE",
    "UNDEFINED_JARGON",
    "MEASUREMENT_UNIT_CONSISTENCY",
    "SUPERLATIVE_EVIDENCE",
    "LOGISTICS_MECHANISM_AUDIT",
    "PROCUREMENT_GEOGRAPHY_FLUCTUATION",
    "CUSTOMER_DEPENDENCY_CONCENTRATION",
    "QA_INSPECTION_CERT_PROCESS",
    "EPF_ESIC_COMPLIANCE_NON_PAYMENT",
    "ARM_LENGTH_RPT_DISCLOSURE",
    "MANAGEMENT_EXPERIENCE_INDIVIDUAL",
    "RAW_MATERIAL_PRICE_VOLATILITY",
    "ORDER_BOOK_AUTHENTICITY",
    "DEPENDENCY_ON_GOVERNMENT_POLICIES",
    "WORKING_CAPITAL_INTENSITY_RATIONALE",
    "FIXED_ASSET_PHYSICAL_VERIFICATION",
    "TOP_10_CLIENTS_RP",
    "EHS_VIOLATIONS_RISK",
    "AUDITOR_RELIANCE_NAMES",
    "REGULATORY_ACTIONS_HISTORY",
    "LITIGATION_COMPLIANCE_STATUS",
    "FINANCIAL_CERTIFICATION_MD",
    "AUDITOR_CHANGE_5YR",
    "PPE_SURGE_RATIONALE",
    "RECEIVABLES_SURGE_RISK",
    "PAT_MARGIN_PEER_BENCHMARK",
    "PAT_MARGIN_PEER_BENCHMARK",
    "KPI_PEER_COMPARISON_RISK",
    "INDUSTRY_REVENUE_BIFURCATION",
    "PRODUCT_TREND_DECLINE",
    "BRANDING_INVESTMENT_QUANTIFICATION",
    "COUNTRY_WISE_IMPORT_TABLE",
    "STATE_WISE_DOMESTIC_DEPENDENCY",
    "OWN_VS_CONTRACTUAL_MANUFACTURING",
    "CUSTOM_MACHINERY_INTERNATIONAL",
    "CHINESE_DISTRIBUTOR_IDENTIFICATION",
    "PRODUCT_USAGE_NVAH",
    "FACTORY_LICENSE_CLEARANCE_GAP",
    "EXCLUSIVE_DISTRIBUTOR_VERIFICATION",
    "CONTINGENT_LIABILITIES_GUARANTEES",
    "RPT_LOANS_ADVANCES",
    "OBJECTS_OF_ISSUE_UTILISATION",
    "KEY_MAN_DEPENDENCY_RISK",
    "MANAGEMENT_EXPERIENCE_JARGON",
    "PROCESS_FLOW_ALIGNMENT",
    "REPETITIVE_TABLE_REMOVAL",
    "PROCESS_LABEL_CONTRADICTION",
    "LEASE_EXPIRY_RISK"
]

NSE_ISSUES = [
    # --- REVIEWER PARITY LAYER (V25 Final) ---
    {
        "id": "MEASUREMENT_UNIT_CONSISTENCY",
        "category": "Forensic",
        "severity": "Critical - Valuation",
        "metric_label": "Unit Consistency",
        "intent": "Data Integrity",
        "primary_evidence_regex": r"(lakhs|crores?|millions?|billions?|₹\s?\d+|sq\.\s?mtrs|sq\.\s?ft|bigha|biswa)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned {snippet}. Kindly review the entire Draft Prospectus (“DP”) and provide uniform disclosure for measurement units across the entire DP. Kindly provide revised draft of disclosure along with confirmation that the same shall be updated in prospectus",
        "mandatory": True
    },
    {
        "id": "IT_SECURITY_CONTRADICTION",
        "category": "Operational",
        "severity": "Critical - Operational",
        "metric_label": "IT Security",
        "intent": "Operational Risk",
        "primary_evidence_regex": r"(information\s+security|cyber\s+security|data\s+protection|IT\s+systems|robust\s+infrastructure)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned {snippet}. Kindly clarify by: (a) providing a 3-year history of security breaches/backups and their financial impact (₹ lakhs and % of net worth); (b) list of active security certifications (ISO 27001) vs actual periodic audits conducted; and (c) detailing the Disaster Recovery (DR) plan and its testing frequency. Provide revised draft.",
        "relocation_hint": "MD&A / Risk Factors",
        "mandatory": False
    },
    {
        "id": "UTILITIES_POWER_WATER",
        "category": "Operational",
        "severity": "Material",
        "metric_label": "Utilities Source",
        "intent": "Dependency Audit",
        "primary_evidence_regex": r"(power|electricity|water|utility|source\s+of)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned utilities for manufacturing. Kindly clarify by: (a) providing the source of power and water (State grid vs Captive vs Private supply); (b) detailing the dependency risk (₹ impact of 1-day outage as % of EBITDA); (c) confirming availability of requisite NOCs/permits for water extraction/discharge. Provide revised draft.",
        "relocation_hint": "Business Overview",
        "mandatory": False
    },
    {
        "id": "AGREEMENT_TO_SELL_LAND",
        "category": "Legal",
        "severity": "Material",
        "metric_label": "Material Agreements",
        "intent": "Asset Audit",
        "primary_evidence_regex": r"(agreement\s+to\s+sell|conveyance\s+deed|land\s+acquisition|title\s+deed)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned material land/asset agreements. Kindly clarify the 'Purpose and Benefit' of such agreements by: (a) detailing the consideration paid vs market value (₹ lakhs and % of total assets); (b) assessing current status of title clear-status; and (c) including a Risk Factor for any delay in possession/conversion. Provide revised draft.",
        "relocation_hint": "Material Contracts",
        "mandatory": False
    },
    {
        "id": "GEOGRAPHIC_REVENUE_SPLIT",
        "category": "Forensic",
        "severity": "Critical - Valuation",
        "metric_label": "Geographic Split",
        "intent": "Materiality",
        "primary_evidence_regex": r"(state-wise|country-wise|geographic|region-wise)\s+revenue",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned geographic revenue. Kindly provide 3-year comparative tables (₹ lakhs and % of total revenue) showing: (a) state-wise break-up for domestic sales; (b) country-wise break-up for international sales; and (c) reconciliation of these tables with 'Segment Reporting' in Financials. Provide revised draft and confirm that the same shall be updated in prospectus.",
        "mandatory": True
    },
    {
        "id": "DOMESTIC_EXPORT_RECON",
        "category": "Forensic",
        "severity": "Critical - Valuation",
        "metric_label": "Domestic vs Export",
        "intent": "Revenue Audit",
        "primary_evidence_regex": r"(domestic|export|international|local)\s+sales",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned Product-wise domestic and export sales bifurcation for the past three financial years and stub period. Kindly reconcile the same with geographic revenue disclosures. Provide revised draft and confirm that the same shall be updated in prospectus.",
        "mandatory": True
    },
    {
        "id": "PRODUCT_TECHNICAL_SEPARATION",
        "category": "Operational",
        "severity": "Critical - Operational",
        "metric_label": "Technical Separation",
        "intent": "Factual Accuracy",
        "primary_evidence_regex": r"(PCU|inverter|solar\s+panels|solar\s+module|technical\s+separation)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned technical product categories. Kindly clarify the 'Technical Separation' by: (a) reconciling overlapping definitions (e.g. PCU vs Inverter vs Hybrid models); (b) providing product-wise technical specifications and market positioning; and (c) quantifying the revenue contribution (₹/%) for each technical sub-category. Provide revised draft.",
        "relocation_hint": "Business Overview",
        "mandatory": False
    },
    {
        "id": "EXPANSION_EXECUTION_STEPS",
        "category": "Operational",
        "severity": "Critical - Operational",
        "metric_label": "Expansion Timeline",
        "intent": "Object Audit",
        "primary_evidence_regex": r"(expansion|new\s+unit|upcoming\s+facility|capacity\s+increase|execution\s+steps)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned {snippet}. Kindly clarify the 'Execution Steps' by: (a) providing a project-wise timeline for new facilities (land/order/commissioning); (b) detailing current progress (%) and capital expenditure incurred vs pending (₹ crores); (c) including a specific Risk Factor for any delay in project commissioning. Provide revised draft.",
        "relocation_hint": "Objects of the Offer / Business Overview",
        "mandatory": True
    },

    # --- OPERATIONAL HYGIENE AGENT (V24 Integration) ---
    {
        "id": "RD_INVESTMENT_DISCLOSURE",
        "category": "Operational",
        "severity": "Critical - Operational",
        "metric_label": "R&D Investment",
        "intent": "Resilience Audit",
        "primary_evidence_regex": r"(research\s+and\s+development|R&D|engineering\s+center)",
        "consolidated_template": "Kindly confirm whether the Company is currently engaged in any research and development (R&D) activities. If yes, kindly provide additional details including the number of employees engaged in the said department and the expenditure incurred on the same in the past three years. Further, provide a revised draft of disclosures along with confirmation that the same will be updated in prospectus",
        "mandatory": False
    },
    {
        "id": "QA_INSPECTION_CERT",
        "category": "Operational",
        "severity": "Critical - Operational",
        "metric_label": "Quality Assurance",
        "intent": "Validation",
        "primary_evidence_regex": r"(quality\s+assurance|quality\s+control|inspection|ISO\s+\d+)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned {snippet}. Kindly clarify by: (a) providing a comparative table of internal inspection logs vs actual rejection rates (₹ impact and % share); (b) list of active QA certifications (ISO/CE) with validity dates; and (c) detailing the impact on cost of production (₹/%) due to quality-led reworks. Provide revised draft.",
        "mandatory": False
    },
    {
        "id": "CUSTOMER_CHURN_REPEAT",
        "category": "Forensic",
        "severity": "Critical - Valuation",
        "metric_label": "Customer Retention",
        "intent": "Revenue Sustainability",
        "primary_evidence_regex": r"(repeat\s+customers|customer\s+retention|churn|recurring\s+revenue)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned {snippet}. Kindly provide a 3-year comparative table showing: (a) % of revenue from repeat customers vs new customers (₹ lakhs and %); (b) customer churn metrics and reason for departure (if >5% impact); and (c) average duration of customer relationship. Provide revised draft.",
        "mandatory": False
    },
    {
        "id": "LOGISTICS_MECHANISM_AUDIT",
        "category": "Operational",
        "severity": "Material",
        "metric_label": "Logistics Mechanism",
        "intent": "Supply Chain",
        "primary_evidence_regex": r"(logistics|warehousing|supply\s+chain|transportation)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned {snippet}. Kindly provide details pertaining to the logistics mechanism of the Company, including the ratio of in-house vs outsourced logistics. Further, provide a revised draft along with confirmation that the same will be updated in prospectus",
        "mandatory": False
    },
    {
        "id": "CSR_BUDGET_EXECUTION",
        "category": "Compliance",
        "severity": "Hygiene",
        "metric_label": "CSR Execution",
        "intent": "Statutory Compliance",
        "primary_evidence_regex": r"(CSR|corporate\s+social\s+responsibility|social\s+spend)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned CSR activities. Kindly confirm whether the allocated amount was expended and specify the quantum thereof for the past three fiscal years. Further, provide a revised draft along with confirmation that the same will be updated in prospectus",
        "relocation_hint": "Legal",
        "mandatory": False
    },
    {
        "id": "ARMS_LENGTH_RPT_DISCLOSURE",
        "category": "Forensic",
        "severity": "Critical - Legal",
        "metric_label": "Arm's Length RPT",
        "intent": "Valuation Integrity",
        "primary_evidence_regex": r"(arm['\s]s\s+length|related\s+party\s+transactions|RPT|group\s+entity)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned related party transactions. Kindly clarify by: (a) providing a 3-year comparative table of all material transactions with group entities (₹ lakhs and % of total cost/revenue); (b) confirming the benchmark pricing mechanism used to ensure arm's length status; and (c) assessing the potential impact on net worth (₹/%) if pricing is non-competitive. Provide revised draft.",
        "relocation_hint": "Related Party Transactions",
        "mandatory": True
    },

    # --- FORENSIC AUDIT: SALES & DISTRIBUTION (V23 Perfect) ---
    {
        "id": "DISTRIBUTION_NETWORK",
        "category": "Operational",
        "severity": "Material",
        "metric_label": "Distribution Health",
        "intent": "Risk Assessment",
        "primary_evidence_regex": r"((?:\d{3,}))\s+(?:distributors|dealers|sales\s+points)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned distributors. Kindly provide no. of distributors (domestic and international) of the Company for the past three financial years and stub period along with confirmation that the same shall be updated in prospectus. Further, kindly provide no. of active and nonactive distributors of the Company for the past three financial years and stub period.",
        "mandatory": True
    },
    {
        "id": "REVENUE_PRODUCT_MISMATCH",
        "category": "Forensic",
        "severity": "Critical - Valuation",
        "metric_label": "Product Revenue Table",
        "intent": "Consistency Check",
        "primary_evidence_regex": r"(revenue\s+from|sales\s+of)\s+(products?|five|six|seven|others)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned {snippet}. Kindly reconcile the binary contradiction by: (a) providing a detailed product-wise reconciliation mapping each product to its respective revenue line (₹ lakhs and % of total revenue); (b) defining the specific composition and cost impact (₹/%) of 'Others' (if >1%); and (c) confirming consistency with financial disclosures across all chapters. Provide revised draft along with confirmation.",
        "mandatory": True
    },

    # --- FORENSIC AUDIT: ENTITY & GROUP (V23 Instinct) ---
    {
        "id": "ENTITY_DESCRIPTION_CONTRADICTION",
        "category": "Forensic",
        "severity": "Material",
        "metric_label": "Entity Classification",
        "intent": "Factual Audit",
        "primary_evidence_regex": r"(NGPL|group\s+company|subsidiary)\s+is\s+(engaged|described|involved)",
        "consolidated_template": "On Page(s) {anchor_pages} of the DRHP, entity '{snippet}' is described. If this entity is classified as 'Food & Beverage' in one section but 'Power Products' in another, kindly reconcile this factual contradiction across all chapters (including 'Group Companies' and 'Related Party Transactions'). Provide revised draft and confirm it will be updated in the prospectus.",
        "relocation_hint": "Group Companies / Related Party Transactions",
        "mandatory": True
    },

    # --- FORENSIC AUDIT: MANUFACTURING & PROCESS ---
    {
        "id": "OPERATIONAL_SCRAP",
        "category": "Operational",
        "severity": "Critical - Operational",
        "metric_label": "Scrap Generation",
        "intent": "Operational Efficiency",
        "primary_evidence_regex": r"(production|manufacturing)\s+process",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned production processes. Kindly clarify the operational cycle by: (a) clarifying the % of scrap/wastage generated and its impact on cost of production (₹/%) and disposal method; (b) confirming if the pictorial flow-chart aligns precisely with the textual steps described (addressing any missing steps like QC/Rework); and (c) reconciling process labels. Provide revised draft and confirm it will be updated in the prospectus.",
        "relocation_hint": "Business Overview / MD&A",
        "mandatory": False
    },

    # --- FORENSIC AUDIT: INTANGIBLES & ASSETS ---
    {
        "id": "TRADEMARK_COVERAGE_GAP",
        "category": "Legal",
        "severity": "Critical - Legal",
        "metric_label": "Intellectual Property",
        "intent": "Risk Assessment",
        "primary_evidence_regex": r"(trademark|registered|brand|IPR)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned registered trademarks. Kindly clarify the status by: (a) confirming if the current registrations cover the current product lineup specifically; (b) detailing any pending renewals/expiries and the potential impact on revenue (₹/%) if rights are lost; and (c) including a corresponding Risk Factor. Provide revised draft and confirm it will be updated in the prospectus.",
        "relocation_hint": "Government and Other Approvals",
        "mandatory": True
    },

    # --- FORENSIC AUDID: INSURANCE & AUDIT ---
    {
        "id": "INSURANCE_AUDIT_MISMATCH",
        "category": "Forensic",
        "severity": "Material",
        "metric_label": "Insurance Coverage",
        "intent": "Resilience Audit",
        "primary_evidence_regex": r"(insurance|coverage|policy|footnote)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned insurance disclosures. Kindly clarify by: (a) providing a 3-year comparative table of historical insurance losses vs claims vs excess payouts (₹/%); and (b) assessing adequacy of cover relative to the scale of operations. Provide revised draft and confirm it will be updated in the prospectus.",
        "mandatory": True
    },

    # --- FORENSIC AUDIT: PRODUCT & SKU RECON (V23 Perfect) ---
    {
        "id": "SKU_RECONCILIATION",
        "category": "Forensic",
        "severity": "Critical - Valuation",
        "metric_label": "Product SKU Count",
        "intent": "Inventory Audit",
        "primary_evidence_regex": r"((?:\d+))\s?(?:skus|stock\s+keeping\s+units)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned {snippet}. However, in the table of product wise bifurcation of revenue on page no. {anchor_pages}, revenue from five products is mentioned. Kindly provide separate disclosures for all six products in the table. Further, kindly define ‘Others’ and provide a revised draft of the table along with confirmation that the same shall be updated in prospectus",
        "mandatory": True
    },
    
    # --- QUANTITATIVE METRICS (Strict quantification) ---
    {
        "id": "SUPPLIER_CONCENTRATION",
        "category": "Operational",
        "severity": "Critical - Valuation",
        "metric_label": "Supplier Concentration",
        "intent": "Risk Assessment",
        "primary_evidence_regex": r"(top\s+\d+|major|critical)\s+suppliers",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned supplier dependency. Kindly provide the following in a tabular format (3 FYs + stub period): (a) list of Top 10 suppliers with ₹ crores and % contribution to total procurement; (b) details of long-term agreements (validity/renewal); and (c) a corresponding Risk Factor. Provide revised draft along with confirmation.",
        "mandatory": True
    },
    {
        "id": "ATTRITION_RATE",
        "category": "HR",
        "severity": "Critical - Operational",
        "metric_label": "Attrition Rate",
        "intent": "Operational Risk",
        "primary_evidence_regex": r"(attrition|turnover|contractual|permanent)\s+employees?",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned employees. Kindly provide the rate of attrition of employees for the last three years and stub period and provide confirmation that the same shall be updated in prospectus. Further, kindly provide details of contractual employees of the Company, if any.",
        "relocation_hint": "MD&A",
        "mandatory": True
    },

    # --- REVENUE & CHANNELS ---
    {
        "id": "REVENUE_CHANNEL_BIFURCATION",
        "category": "Forensic",
        "severity": "Critical - Valuation",
        "metric_label": "Revenue Bifurcation",
        "intent": "Materiality",
        "primary_evidence_regex": r"(revenue\s+from|sales\s+in)\s+(b2b|b2c|direct|dealer)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned sales channels. Kindly provide whether the Company is engaged in direct sales also. If yes, kindly provide B2B and B2C revenue bifurcation for the past three financial years and stub period along with confirmation that the same shall be updated in prospectus.",
        "mandatory": True
    },

    # --- STANDARD HYGIENE ---
    {
        "id": "CAPACITY_CERTIFICATION",
        "category": "Operational",
        "severity": "Critical - Valuation",
        "metric_label": "Capacity Certification",
        "intent": "Validation",
        "primary_evidence_regex": r"(installed\s+capacity|actual\s+production|utili[zs]ation)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned production capacity. Kindly clarify by: (a) providing product-wise and unit-wise capacity utilization metrics along with % for past three years and stub period; (b) confirming if figures are certified by an independent chartered engineer; and (c) including an 'Under-utilization' Risk Factor if utilization is low. Provide revised draft and confirm it will be updated in the prospectus.",
        "relocation_hint": "Business Overview",
        "mandatory": True
    },
    {
        "id": "SUPERLATIVE_EVIDENCE",
        "category": "Marketing",
        "severity": "Hygiene",
        "metric_label": "Superlative Claims",
        "intent": "Evidence Hunt",
        "primary_evidence_regex": r"\b(leader|key\s+player|strong\s+foothold|innovative|seasoned|extensive|trusted|robust|significant|High-quality|comprehensive|future-proof|experienced|superior)\b",
        "consolidated_template": "In “Our Business” chapter- It is observed that the Company has made use of superlative words / adjectives like {snippet} etc. without citing the source and basis of the same as per the instructions mentioned in Schedule VI of the SEBI (ICDR) Regulations 2018 in relation to forward-looking statements. Kindly provide the source/basis of all such statements/claims. Also include these bases in the Material Documents Chapter available for inspection. If not, kindly review and revise the same. Further, the above mentioned points are merely indicative in nature, the Merchant banker shall vet the offer document and ensure that there are no disclosures which are advertising statements and marketing statement and if there are any it shall be either be drafted in a neutral language or provide a basis for the same or removed, to that end, kindly provide a draft along with a confirmation the same shall be placed at the time of prospectus as applicable",
        "mandatory": True
    },
    {
        "id": "UNDEFINED_JARGON",
        "category": "Hygiene",
        "severity": "Hygiene",
        "intent": "Definition Policing",
        "primary_evidence_regex": r"\b([A-Z]{3,6})\b", 
        "consolidated_template": "It has been observed that words such as {snippet} etc. has been used in DP however the same are not defined. Kindly review the entire DP and define the full form of all such words in ‘Definition and Abbreviations’ chapter and provide confirmation that the same shall be updated in prospectus.",
        "exclusions": ["NSE", "SEBI", "DRHP", "ASBA", "PAN", "DIN", "GST", "EPF", "ESIC", "CRISIL", "ICDR", "INR", "FY", "AND", "BUT", "ONLY", "THE", "FOR", "WITH", "FROM", "HOME", "UNIT", "SITE", "VIA", "HOUSE", "CATER", "YEARS", "SET", "BELOW", "SYSTEM", "ISO", "COVERS", "LIKE", "IMPACT", "TRUST", "AMONG", "DAY", "PER", "ONCE", "SETUP", "HANDLE", "MEDIUM", "WIDE", "RANGE", "OFFER", "MUMBAI", "WATER", "SUPPLY", "WHILE", "CLOSE", "TIMES", "LONG", "TERM", "LINE", "LAND", "AREA", "LPG", "CNG"]
    },
    {
        "id": "LEASE_STATUS_MANDATORY",
        "category": "Legal",
        "severity": "Material",
        "primary_evidence_regex": r"(lease|rental|registered\s+office|premises)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned {snippet}. Kindly disclose in a tabular format, details of all properties leased along with details of lessor, lease tenure, lease rent, whether lessor is a related party (including whether a member of the promoter/ promoter group), whether lease deed is adequately stamped/ registered and provide a revised draft along with confirmation that the same shall be updated in prospectus",
        "mandatory": True
    },
    {
        "id": "SUBSIDIARY_RATIONALE",
        "category": "Governance",
        "severity": "Material",
        "primary_evidence_regex": r"(subsidiary|group\s+entity|joint\s+venture)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned {snippet}. Kindly clarify the rationale for the existing corporate structure and the reasons for not undertaking business operations directly through the Issuer Company. Further, provide a revised draft along with confirmation.",
        "mandatory": True
    },
    {
        "id": "REVENUE_MODEL_EXPLANATION",
        "category": "Forensic",
        "severity": "Critical - Valuation",
        "primary_evidence_regex": r"(revenue\s+model|business\s+model|how\s+we\s+make\s+money)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned the Revenue Model. Kindly provide a more granular explanation including: (a) transaction-wise fee structure vs recurring revenue; (b) key revenue drivers and their sensitivity; and (c) reconciliation with segment-wise reporting. Provide revised draft along with confirmation.",
        "mandatory": True
    },
    {
        "id": "PROCUREMENT_GEOGRAPHY_FLUCTUATION",
        "category": "Operational",
        "severity": "Material",
        "primary_evidence_regex": r"(procurement|raw\s+material|sourcing|import|domestic\s+purchase)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned raw materials procurement. Kindly provide geographic bifurcation of raw materials procurement along with % of supplies for the past three financial years and stub period. Further, clarify the impact of currency fluctuation and whether there are any long-term agreements with suppliers. Provide revised draft and confirmation that the same shall be updated in prospectus.",
        "mandatory": True
    },
    {
        "id": "QA_INSPECTION_CERT_PROCESS",
        "category": "Quality",
        "severity": "Material",
        "primary_evidence_regex": r"(quality\s+control|QA|QC|inspection|certification|ISO\s+\d+)",
        "consolidated_template": "On page no. {anchor_pages}, quality assurance processes are discussed. Kindly elaborate on the Company’s quality assurance and control mechanisms. If the Company lacks in-house quality certifications, kindly provide the rationale and consider the inclusion of a risk factor. Further, provide a revised draft along with confirmation.",
        "mandatory": True
    },
    {
        "id": "MANAGEMENT_EXPERIENCE_INDIVIDUAL",
        "category": "Governance",
        "severity": "Material",
        "primary_evidence_regex": r"((?:\d{2}))\s+(?:decades|years)\s+of\s+(?:combined|collective)\s+experience",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned {snippet}. As per drafting norms, kindly provide individual years of experience, specific domain expertise, and prior successful track record for each Key Managerial Personnel (KMP). Avoid generic aggregation. Provide revised draft and confirmation.",
        "mandatory": True
    },
    {
        "id": "RAW_MATERIAL_PRICE_VOLATILITY",
        "category": "Operational",
        "severity": "Material",
        "primary_evidence_regex": r"(raw\s+material|input\s+cost|price\s+volatility|cost\s+of\s+goods)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned raw material price volatility. Kindly quantify the impact of a 5% and 10% increase in input costs on the restated EBITDA for the last 3 fiscal years. Also, clarify the pass-through mechanism to customers. Provide revised draft.",
        "mandatory": True
    },
    {
        "id": "ORDER_BOOK_AUTHENTICITY",
        "category": "Forensic",
        "severity": "Critical - Valuation",
        "primary_evidence_regex": r"(order\s+book|contracts\s+in\s+hand|backlog|pending\s+orders)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned {snippet}. Kindly provide a 3-year comparative table showing: (a) fresh orders received; (b) orders executed; (c) orders cancelled/modified; and (d) verification process for order book authenticity by statutory auditors. Provide revised draft.",
        "mandatory": True
    },
    {
        "id": "DEPENDENCY_ON_GOVERNMENT_POLICIES",
        "category": "Risk",
        "severity": "Material",
        "primary_evidence_regex": r"(government\s+policy|regulatory\s+framework|subsidies|incentives|PLI)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned reliance on government policies/incentives. Kindly provide the ₹ impact and % of revenue/profit derived from specific government schemes (like PLI) for the last 3 years and stub period. Clarify the impact of potential withdrawal of such schemes. Provide revised draft.",
        "mandatory": True
    },
    {
        "id": "WORKING_CAPITAL_INTENSITY_RATIONALE",
        "category": "Forensic",
        "severity": "Critical - Valuation",
        "primary_evidence_regex": r"(working\s+capital|inventory\s+days|debtor\s+days|current\s+assets)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned working capital requirements. Kindly provide a detailed rationale for inventory/debtor days being significantly higher/lower than industry peers. Include a 3-year comparative table mapping cash conversion cycle with operating cash flows. Provide revised draft.",
        "mandatory": True
    },
    {
        "id": "FIXED_ASSET_PHYSICAL_VERIFICATION",
        "category": "Forensic",
        "severity": "Material",
        "primary_evidence_regex": r"(physical\s+verification|fixed\s+assets|property\s+plant\s+equipment)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned fixed assets. Kindly clarify the frequency of physical verification of fixed assets by management and whether any material discrepancies were noted in the last 3 fiscal years. Provide a certification from the statutory auditor regarding the same. Provide revised draft.",
        "mandatory": True
    },
    {
        "id": "EPF_ESIC_COMPLIANCE_NON_PAYMENT",
        "category": "Compliance",
        "severity": "Material",
        "primary_evidence_regex": r"(EPF|ESIC|provident\s+fund|statutory\s+dues)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned statutory dues. Kindly provide details of the Company’s contributions towards the Employees’ Provident Fund (EPF) and Employees’ State Insurance Corporation (ESIC) for the past three fiscal years along with confirmation that the same shall be updated in prospectus.",
        "mandatory": True
    },
    {
        "id": "TOP_10_CLIENTS_RP",
        "category": "Forensic",
        "severity": "Critical - Valuation",
        "primary_evidence_regex": r"(top\s+10|major|key)\s+(clients?|customers?)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned top 10 clients. Kindly disclose details (including names) of top 10 clients in Our Business section. Further, disclose wherever any top 10 customer or supplier is a related party. Provide revised draft.",
        "mandatory": True
    },
    {
        "id": "EHS_VIOLATIONS_RISK",
        "category": "Compliance",
        "severity": "Material",
        "primary_evidence_regex": r"(environment|health|safety|EHS|pollution|violation|penalty)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned EHS compliance. Kindly disclose details of all past violations for environment, health and safety (EHS) laws and regulations. Disclose a suitable risk factor in this regard, if material. Provide revised draft.",
        "mandatory": True
    },
    {
        "id": "AUDITOR_RELIANCE_NAMES",
        "category": "Governance",
        "severity": "Material",
        "primary_evidence_regex": r"(statutory\s+auditor|reliance|other\s+auditors|examination\s+report)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned statutory auditors. Kindly disclose names of other auditors who have audited financial statements which have been relied on by statutory auditor for the purpose of issuing examination report on restated consolidated financial information. Provide revised draft.",
        "mandatory": True
    },
    {
        "id": "REGULATORY_ACTIONS_HISTORY",
        "category": "Compliance",
        "severity": "Material",
        "primary_evidence_regex": r"(violations|actions|statutory\s+authorities|regulatory\s+authorities|penalty|show\s+cause)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned violations/actions. Kindly disclose in detail, all violations and actions taken by statutory or regulatory authorities against the company. Provide revised draft.",
        "mandatory": True
    },
    {
        "id": "LITIGATION_COMPLIANCE_STATUS",
        "category": "Legal",
        "severity": "Material",
        "primary_evidence_regex": r"(litigations|court|tribunal|pending\s+cases|legal\s+actions)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned material litigations. Kindly disclose updated status of other material litigations against the company including any action against the company and any action taken by company to ensure compliance required in terms of litigations. Provide revised draft.",
        "mandatory": True
    },
    {
        "id": "FINANCIAL_CERTIFICATION_MD",
        "category": "Governance",
        "severity": "Material",
        "primary_evidence_regex": r"(financial\s+information|certified|chartered\s+accountant|statutory\s+auditor)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned financial information. Kindly ensure and confirm that all financial information disclosed in DRHP is certified by Chartered accountant/ statutory auditor of the company and such certificates shall form part of material documents available for inspection. Provide revised draft.",
        "mandatory": True
    },
    {
        "id": "AUDITOR_CHANGE_5YR",
        "category": "Governance",
        "severity": "Material",
        "primary_evidence_regex": r"(change\s+in\s+auditor|resignation|appointment\s+of\s+auditor)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned statutory auditors. Kindly confirm whether there has been a change in auditor(s) before completion of the appointed term (in any of the past five fiscal years), and the reasons thereof. Provide revised draft.",
        "mandatory": True
    },
    {
        "id": "PPE_SURGE_RATIONALE",
        "category": "Risk",
        "severity": "Material",
        "primary_evidence_regex": r"(property|plant|equipment|PPE|fixed\s+assets|increase\s+in\s+assets)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned property / plant and equipment. Kindly disclose the reason for substantial increase in the same and source of fund as a Risk Factor. Provide revised draft.",
        "mandatory": True
    },
    {
        "id": "RECEIVABLES_SURGE_RISK",
        "category": "Risk",
        "severity": "Material",
        "primary_evidence_regex": r"(trade\s+receivables|debtors|outstanding\s+dues)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned trade receivables. Kindly disclose the reason for substantial increase in trade receivables as Risk Factor. Provide revised draft.",
        "mandatory": True
    },
    {
        "id": "PAT_MARGIN_PEER_BENCHMARK",
        "category": "Risk",
        "severity": "Material",
        "primary_evidence_regex": r"(PAT\s+margin|profitability|industry\s+standards|peer\s+benchmark)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned PAT margin. Kindly disclose the PAT margin vis a vis industry standards as Risk Factor. Provide revised draft.",
        "mandatory": True
    },
    {
        "id": "KPI_PEER_COMPARISON_RISK",
        "category": "Risk",
        "severity": "Material",
        "primary_evidence_regex": r"(KPI|key\s+performance\s+indicators|comparable\s+companies|peers)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned comparable companies. Kindly disclose those parameter which are better KPI as a Risk Factor for comparable companies. Provide revised draft.",
        "mandatory": True
    },
    {
        "id": "INDUSTRY_REVENUE_BIFURCATION",
        "category": "Forensic",
        "severity": "Critical - Valuation",
        "primary_evidence_regex": r"(automotive|toy|foam|healthcare|construction|segments)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned industry-wise revenue. Kindly provide the details of breakup of industry-wise revenue from operations split for the past three financial years and stub period including automotive, consumer home appliances, construction equipment, farm equipment, healthcare segments and from toys making etc. Provide revised draft.",
        "mandatory": True
    },
    {
        "id": "PRODUCT_TREND_DECLINE",
        "category": "Risk",
        "severity": "Critical - Operational",
        "primary_evidence_regex": r"(revenue|sales|profit)\s+decline",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned {snippet}. Kindly provide detailed reasons for the substantial decline in revenue from {snippet} observed in FY 2025 as compared to FY 2024. Provide revised draft.",
        "mandatory": True
    },
    {
        "id": "BRANDING_INVESTMENT_QUANTIFICATION",
        "category": "Operational",
        "severity": "Material",
        "primary_evidence_regex": r"(branding|marketing|advertising|promotion)\s+expenditure",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned R&D and branding. Kindly provide details of R&D and branding investment/expenditure done in the past three financial years and stub period. Ensure ₹ and % quantification relative to total revenue. Provide revised draft.",
        "mandatory": True
    },
    {
        "id": "COUNTRY_WISE_IMPORT_TABLE",
        "category": "Forensic",
        "severity": "Critical - Valuation",
        "primary_evidence_regex": r"(import|purchases|sourcing|foreign)\s+procurement",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned import purchases. Kindly incorporate the details of country-wise import purchases value and % terms for the past three financial years and stub period. Provide revised draft.",
        "mandatory": True
    },
    {
        "id": "STATE_WISE_DOMESTIC_DEPENDENCY",
        "category": "Operational",
        "severity": "Material",
        "primary_evidence_regex": r"(domestic\s+purchase|local\s+suppliers|raw\s+material\s+sourcing)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned domestic purchases. Kindly include the state-wise dependency of domestic purchases for the past three financial years and stub period. Analyze the impact of supply chain disruptions in key states. Provide revised draft.",
        "mandatory": True
    },
    {
        "id": "OWN_VS_CONTRACTUAL_MANUFACTURING",
        "category": "Operational",
        "severity": "Material",
        "primary_evidence_regex": r"(own\s+manufacturing|contractual\s+manufacturing|outsourced\s+production)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned manufacturing verticals. Kindly check for inclusion of details of major verticals split into own manufacturing and contractual manufacturing. Provide ₹ and % split for each major product line. Provide revised draft.",
        "mandatory": True
    },
    {
        "id": "CUSTOM_MACHINERY_INTERNATIONAL",
        "category": "Operational",
        "severity": "Material",
        "primary_evidence_regex": r"(custom\s+machinery|specialized\s+equipment|global\s+customers)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned specialized equipment. Kindly elaborate and explain the statement 'Custom Machinery for International Clients'. Clarify the CAPEX and timeline for the same. Provide revised draft.",
        "mandatory": False
    },
    {
        "id": "CHINESE_DISTRIBUTOR_IDENTIFICATION",
        "category": "Compliance",
        "severity": "Material",
        "primary_evidence_regex": r"(Chinese\s+distributor|imported\s+from\s+China|China\s+sales)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned {snippet}. Kindly check for inclusion/provide the name and detailed profile of such Chinese distributor. Clarify any regulatory/geopolitical risks associated. Provide revised draft.",
        "mandatory": False
    },
    {
        "id": "PRODUCT_USAGE_NVAH",
        "category": "Operational",
        "severity": "Material",
        "primary_evidence_regex": r"(NVAH|product\s+usage|application)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned NVAH details. Kindly include the details of Product usage in NVAH. Map specific product lines to NVAH applications and their revenue contribution. Provide revised draft.",
        "mandatory": False
    },
    {
        "id": "FACTORY_LICENSE_CLEARANCE_GAP",
        "category": "Compliance",
        "severity": "Critical - Legal",
        "primary_evidence_regex": r"(factory\s+license|clearances|Unit\s+II|license\s+issue)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned Unit II license. Kindly include the details of factory license for Unit II and provide rationale for how the company is operating without the same in place. Further, provide confirmation whether the issuer has received crucial clearances. Provide revised draft.",
        "mandatory": True
    },
    {
        "id": "PROPERTY_AREA_UNIT_SPECIFIC",
        "category": "Forensic",
        "severity": "Hygiene",
        "primary_evidence_regex": r"(property|area|leased|premises)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned property section. Kindly include the area details (i.e. sq.ft., sq. meters etc.) for each material property and ensure unit consistency. Provide revised draft.",
        "mandatory": True
    },
    {
        "id": "GOVERNMENT_POLICIES_INCENTIVES",
        "category": "Compliance",
        "severity": "Material",
        "primary_evidence_regex": r"(government\s+polic|incentive|scheme|subsidy|PLI|tax\s+benefit)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned government policies. Kindly provide the details of government policies/ any benefit in past 3 financial years and stub period related to its key product line of toys and foam based products manufactured. Provide revised draft.",
        "mandatory": True
    },
    {
        "id": "CONTINGENT_LIABILITIES_GUARANTEES",
        "category": "Forensic",
        "severity": "Critical - Valuation",
        "primary_evidence_regex": r"(contingent\s+liabilit|corporate\s+guarantee|bank\s+guarantee|performance\s+guarantee|letter\s+of\s+comfort)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned contingent liabilities / guarantees. Kindly provide: (a) nature and beneficiary of each guarantee; (b) ₹ amount and % of net worth; (c) tenure and trigger conditions; and (d) corresponding Risk Factor, if material. Provide revised draft.",
        "mandatory": True
    },
    {
        "id": "RPT_LOANS_ADVANCES",
        "category": "Forensic",
        "severity": "Critical - Legal",
        "primary_evidence_regex": r"(loan|advance|inter\s+corporate|ICD)\s+(to|from)\s+(promoter|group|subsidiary)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned loans/advances to related parties. Kindly clarify: (a) purpose and commercial rationale; (b) interest rate vs market benchmark; (c) repayment status and recoverability; and (d) confirmation whether these are at arm’s length. Provide revised draft.",
        "mandatory": True
    },
    {
        "id": "OBJECTS_OF_ISSUE_UTILISATION",
        "category": "Governance",
        "severity": "Critical - Valuation",
        "primary_evidence_regex": r"(objects\s+of\s+the\s+issue|utilisation\s+of\s+proceeds|fund\s+deployment)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned Objects of the Issue. Kindly provide: (a) project-wise deployment schedule (₹ and timeline); (b) monitoring mechanism (internal/monitoring agency); (c) confirmation on handling deviations, if any. Provide revised draft.",
        "mandatory": True
    },
    {
        "id": "KEY_MAN_DEPENDENCY_RISK",
        "category": "Risk",
        "severity": "Material",
        "primary_evidence_regex": r"(promoter|key\s+managerial|founder)\s+(drives|leads|manages)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned {snippet}. Kindly assess and disclose key-man dependency risk and succession planning, if any. Provide revised draft.",
        "mandatory": False
    },
    {
        "id": "MANAGEMENT_EXPERIENCE_JARGON",
        "category": "Hygiene",
        "severity": "Hygiene",
        "primary_evidence_regex": r"(seasoned\s+experts|experts\s+in\s+power\s+electronics)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned {snippet}. Kindly define ‘seasoned experts’ and provide a revised draft.",
        "mandatory": False
    },
    {
        "id": "PROCESS_FLOW_ALIGNMENT",
        "category": "Operational",
        "severity": "Material",
        "primary_evidence_regex": r"(pictorial\s+chart|process\s+flow)\s+(defined|below)",
        "consolidated_template": "On page no. {anchor_pages}, it has been observed that the pictorial chart and the process flow defined below the same are not in line. Kindly review and share the revised draft along with confirmation that the same shall be updated in prospectus",
        "mandatory": False
    },
    {
        "id": "REPETITIVE_TABLE_REMOVAL",
        "category": "Hygiene",
        "severity": "Hygiene",
        "primary_evidence_regex": r"(table|data)\s+is\s+repetitive",
        "consolidated_template": "It has been observed that the table provided on page no. {anchor_pages} is repetitive in nature. Kindly review and remove the same and provide confirmation that the same shall be updated in prospectus",
        "mandatory": False
    },
    {
        "id": "PROCESS_LABEL_CONTRADICTION",
        "category": "Forensic",
        "severity": "Material",
        "primary_evidence_regex": r"(TRANSFORMER\s+PRODUCTION\s+PROCESS|assembles\s+inverters)",
        "consolidated_template": "On page no. {anchor_pages}, it is mentioned “TRANSFORMER PRODUCTION PROCESS” however the Company assembles inverters. Kindly review and clarify.",
        "mandatory": True
    },
    {
        "id": "LEASE_EXPIRY_RISK",
        "category": "Legal",
        "severity": "Critical - Operational",
        "primary_evidence_regex": r"(validity\s+of\s+lease|expired|about\s+to\s+expire)",
        "consolidated_template": "It has been observed that the validity of lease agreement of Warehouse has already expired. Further, the lease agreement for the assembling unit is about to expire. Kindly provide the current status of both the properties and disclose the impact on the business if these are not renewed. Kindly review and provide a revised draft along with confirmation that the same shall be updated in prospectus.",
        "mandatory": True
    }
]

# ICDR RULES (Compatibility)
ICDR_RULES = {
    "eligibility": "Regulation 6: Eligibility requirements for an initial public offer.",
    "promoter_contribution": "Regulation 14: Minimum promoters' contribution shall be 20% of post-issue capital.",
    "lock_in": "Regulation 16: Promoters' contribution shall be locked in for 18 months.",
}
