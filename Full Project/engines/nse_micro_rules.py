# engines/nse_micro_rules.py

MICRO_RULES = [
    {
        "id": "LEASE_EXPIRY_RISK",
        "trigger_regex": r"(lease\s+expiry|lease\s+period|expires\s+on\s+Dec|expires\s+in\s+2025)",
        "query": "Kindly provide the current status of lease renewal and assess the impact on business continuity if the same is not renewed. Provide revised draft."
    },
    {
        "id": "REDUNDANT_TABLE",
        "trigger_regex": r"(repetitive\s+table|same\s+table|duplicate\s+data)", # Usually detected by logic, but adding regex for manual markers
        "query": "It has been observed that the table appears repetitive in nature. Kindly review and remove the same. Provide revised draft."
    },
    {
        "id": "PRODUCT_DESCRIPTION_MISSING",
        "trigger_regex": r"(contributes?\s+to\s+revenue|revenue\s+share)\s+but\s+not\s+described",
        "query": "The product contributes to revenue but is not described in the Business Overview. Kindly provide detailed disclosure. Provide revised draft."
    },
    {
        "id": "FOOTNOTE_MISMATCH",
        "trigger_regex": r"(\*\s|\#\s|\†\s|\‡\s)(?!.*(?:footnote|refer\s+to|below))",
        "query": "The footnote symbol is not referenced in the table. Kindly reconcile the same. Provide revised draft."
    },
    {
        "id": "COLLECTIVE_EXPERIENCE",
        "trigger_regex": r"(collective\s+experience|combined\s+experience|team\s+experience)\s+of\s+\d+",
        "query": "Kindly consider providing individual experience instead of collective experience. Provide revised draft."
    },
    {
        "id": "EXCLUSIVE_DISTRIBUTOR_BACKUP",
        "trigger_regex": r"(exclusive\s+distributor|sole\s+distributor|exclusive\s+rights)",
        "query": "Kindly provide adequate documentary back-up for the exclusive distributor claim. Provide revised draft."
    },
    {
        "id": "WHY_NOT_ISSUER",
        "trigger_regex": r"(subsidiary\s+undertakes|operations\s+of\s+subsidiary|subsidiary\s+engaged)",
        "query": "Kindly clarify the rationale for not undertaking operations directly through the Issuer Company. Provide revised draft."
    }
]
