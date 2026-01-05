# engines/business_model_classifier.py

class BusinessModelClassifier:
    """
    V26: Business Model Hard Gate.
    Determines if the DRHP belongs to MANUFACTURING, TRADING_DISTRIBUTION, SERVICES, or HYBRID.
    Uses rule-based count thresholds for high reliability.
    """
    
    def classify(self, pages_text):
        # Extract first 10 pages for classification
        top_pages = sorted(pages_text.keys(), key=lambda x: int(x))[:10]
        context = " ".join([pages_text[p] for p in top_pages]).lower()
        
        # Keyword Lists
        m_keywords = ["manufacturing", "factory", "plant", "installed capacity", "production", "raw material", "machinery", "assembly", "scrap", "unit-wise"]
        t_keywords = ["trading", "retail", "wholesale", "distributor", "purchase of stock", "dealer", "procurement", "resale", "stockists"]
        s_keywords = ["service", "software", "manpower", "platform", "consultancy", "solution provider", "centres", "fees", "subscription", "recurring"]
        
        scores = {
            "MANUFACTURING": sum(1 for k in m_keywords if k in context),
            "TRADING_DISTRIBUTION": sum(1 for k in t_keywords if k in context),
            "SERVICES": sum(1 for k in s_keywords if k in context)
        }
        
        # Classification thresholds
        best_fit = "HYBRID"
        max_score = 0
        
        for model, score in scores.items():
            if score >= 2 and score > max_score:
                max_score = score
                best_fit = model
                
        print(f"[*] Business Model Classified: {best_fit} (Scores: {scores})")
        return best_fit

# Rules Mapping (V27: Widened for Procedural Growth)
# Any query in MANDATORY_BUSINESS_OVERVIEW should generally bypass this gate.
RULES_ALLOWED = {
    "MANUFACTURING": [
        "CAPACITY_CERTIFICATION", "UTILITIES_POWER_WATER", "QA_INSPECTION_CERT_PROCESS", 
        "OPERATIONAL_SCRAP", "RD_INVESTMENT_DISCLOSURE", "SKU_RECONCILIATION",
        "PROCUREMENT_GEOGRAPHY_FLUCTUATION", "LOGISTICS_MECHANISM_AUDIT",
        "REVENUE_MODEL_EXPLANATION", "SUPPLIER_CONCENTRATION", "ATTRITION_RATE",
        "PRODUCT_WISE_REVENUE_TABLE", "REVENUE_CHANNEL_BIFURCATION"
    ],
    "TRADING_DISTRIBUTION": [
        "SUPPLIER_CONCENTRATION", "DISTRIBUTOR_HEALTH_DETAIL", "LOGISTICS_MECHANISM_AUDIT",
        "REVENUE_CHANNEL_BIFURCATION", "SKU_RECONCILIATION", "ATTRITION_RATE",
        "REVENUE_MODEL_EXPLANATION", "PRODUCT_WISE_REVENUE_TABLE"
    ],
    "SERVICES": [
        "ATTRITION_RATE", "CUSTOMER_CHURN_REPEAT", "IT_SECURITY_CONTRADICTION",
        "PRODUCT_TECHNICAL_SEPARATION", "REVENUE_MODEL_EXPLANATION",
        "SKU_RECONCILIATION", "PRODUCT_WISE_REVENUE_TABLE"
    ],
    "HYBRID": None # All rules allowed if hybrid
}
