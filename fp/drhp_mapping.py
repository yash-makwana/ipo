"""
DRHP Mapping - Smart Retrieval Configuration
=============================================
"""

DRHP_CHAPTER_MAPPINGS = {
    "CHAPTER_II_RISK_FACTORS": {
        "drhp_chapter_name": "CHAPTER II – RISK FACTORS",
        "description": "Material risks and uncertainties",
        
        "neo4j_filters": {
            "ICDR": {
                "chapters": ["Chapter II"],
                "mandatory_only": True,
                "max_obligations": 30,  # ✅ Cap at 30 instead of 200
                "use_smart_retrieval": True  # ✅ Use relevance filtering
            },
            "Companies Act": {
                "chapters": [],
                "mandatory_only": False,
                "max_obligations": 0,
                "use_smart_retrieval": False
            }
        }
    },
    
    "CHAPTER_V_ABOUT_COMPANY": {
        "drhp_chapter_name": "CHAPTER V – ABOUT THE COMPANY",
        "description": "Business, operations, management, and structure",
        
        "neo4j_filters": {
            "ICDR": {
                "chapters": ["Chapter II"],
                "mandatory_only": True,
                "max_obligations": 40,  # ✅ Slightly more for this chapter
                "use_smart_retrieval": True
            },
            "Companies Act": {
                "chapters": [],
                "mandatory_only": False,
                "max_obligations": 0,
                "use_smart_retrieval": False
            }
        }
    },
    
    "CHAPTER_VI_FINANCIAL": {
        "drhp_chapter_name": "CHAPTER VI – FINANCIAL INFORMATION",
        "description": "Financial statements, obligations, and material changes",
        
        "neo4j_filters": {
            "ICDR": {
                "chapters": ["Chapter II", "Chapter IX"],
                "mandatory_only": True,
                "max_obligations": 50,  # ✅ More for financial chapter
                "use_smart_retrieval": True
            },
            "Companies Act": {
                "chapters": [],
                "mandatory_only": False,
                "max_obligations": 0,
                "use_smart_retrieval": False
            }
        }
    },
    
    "CHAPTER_VII_LEGAL": {
        "drhp_chapter_name": "CHAPTER VII – LEGAL INFORMATION",
        "description": "Legal proceedings and regulatory compliance",
        
        "neo4j_filters": {
            "ICDR": {
                "chapters": ["Chapter II"],
                "mandatory_only": True,
                "max_obligations": 30,
                "use_smart_retrieval": True
            },
            "Companies Act": {
                "chapters": [],
                "mandatory_only": False,
                "max_obligations": 0,
                "use_smart_retrieval": False
            }
        }
    },
    
    "CHAPTER_VIII_ISSUE": {
        "drhp_chapter_name": "CHAPTER VIII – ISSUE INFORMATION",
        "description": "Offering structure and terms",
        
        "neo4j_filters": {
            "ICDR": {
                "chapters": ["Chapter I", "Chapter II", "Chapter IV"],
                "mandatory_only": True,
                "max_obligations": 40,
                "use_smart_retrieval": True
            },
            "Companies Act": {
                "chapters": [],
                "mandatory_only": False,
                "max_obligations": 0,
                "use_smart_retrieval": False
            }
        }
    }
}


def get_regulations_for_drhp_section(drhp_chapter: str, drhp_subchapter: str = None):
    """Get mapping WITHOUT hardcoded checks"""
    if drhp_chapter not in DRHP_CHAPTER_MAPPINGS:
        return None
    
    return DRHP_CHAPTER_MAPPINGS[drhp_chapter]


def get_all_drhp_chapters():
    """Get list of all DRHP chapters"""
    return [
        {
            "key": key,
            "name": value["drhp_chapter_name"],
            "description": value.get("description", "")
        }
        for key, value in DRHP_CHAPTER_MAPPINGS.items()
    ]


def get_neo4j_filters_for_chapter(drhp_chapter: str, regulation_type: str = "ICDR"):
    """Get Neo4j filters for dynamic obligation retrieval"""
    mapping = get_regulations_for_drhp_section(drhp_chapter)
    if not mapping:
        return {
            "chapters": [], 
            "mandatory_only": False,
            "max_obligations": 30,
            "use_smart_retrieval": True
        }
    
    filters = mapping.get("neo4j_filters", {}).get(regulation_type, {})
    return {
        "chapters": filters.get("chapters", []),
        "mandatory_only": filters.get("mandatory_only", False),
        "max_obligations": filters.get("max_obligations", 30),  
        "use_smart_retrieval": filters.get("use_smart_retrieval", True) 
    }