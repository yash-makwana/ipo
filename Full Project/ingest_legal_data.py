# ingest_legal_data.py
# Run this in Cloud Shell to populate Neo4j with legal data

from db_config import get_neo4j_connection
import uuid

def generate_id():
    """Generate a unique ID"""
    return str(uuid.uuid4())[:8]

def ingest_icdr_regulations():
    """Ingest ICDR Regulations structure into Neo4j"""
    
    conn = get_neo4j_connection()
    
    print("🚀 Starting ICDR Regulations ingestion...")
    
    # Step 1: Create Regulation node
    regulation_id = "ICDR_2018"
    conn.query("""
        MERGE (r:Regulation {id: $id})
        SET r.name = $name,
            r.type = $type,
            r.year = $year,
            r.description = $description
    """, {
        'id': regulation_id,
        'name': 'ICDR',
        'type': 'SEBI Regulation',
        'year': 2018,
        'description': 'Issue of Capital and Disclosure Requirements Regulations'
    })
    
    print("✓ Created Regulation: ICDR")
    
    # Step 2: Create Chapters
    chapters = [
        {
            'id': 'ICDR_CH1',
            'number': '1',
            'title': 'Preliminary',
            'description': 'Short title, commencement, and definitions'
        },
        {
            'id': 'ICDR_CH2',
            'number': '2',
            'title': 'Public Issue',
            'description': 'Requirements for public issue of equity shares'
        },
        {
            'id': 'ICDR_CH3',
            'number': '3',
            'title': 'Offer for Sale',
            'description': 'Offer for sale of securities'
        },
        {
            'id': 'ICDR_CH4',
            'number': '4',
            'title': 'Issue of Indian Depository Receipts',
            'description': 'Requirements for IDR issuance'
        },
        {
            'id': 'ICDR_CH5',
            'number': '5',
            'title': 'Pricing',
            'description': 'Pricing of securities'
        }
    ]
    
    for chapter in chapters:
        conn.query("""
            MERGE (c:Chapter {id: $id})
            SET c.number = $number,
                c.title = $title,
                c.description = $description
            WITH c
            MATCH (r:Regulation {id: $reg_id})
            MERGE (r)-[:HAS_CHAPTER]->(c)
        """, {
            'id': chapter['id'],
            'number': chapter['number'],
            'title': chapter['title'],
            'description': chapter['description'],
            'reg_id': regulation_id
        })
        print(f"✓ Created Chapter {chapter['number']}: {chapter['title']}")
    
    # Step 3: Create SubChapters for Chapter 2 (Public Issue)
    subchapters = [
        {
            'id': 'ICDR_CH2_A',
            'number': '2A',
            'title': 'Eligibility Requirements',
            'chapter_id': 'ICDR_CH2'
        },
        {
            'id': 'ICDR_CH2_B',
            'number': '2B',
            'title': 'Disclosures in Offer Document',
            'chapter_id': 'ICDR_CH2'
        },
        {
            'id': 'ICDR_CH2_C',
            'number': '2C',
            'title': 'Issue Procedure',
            'chapter_id': 'ICDR_CH2'
        }
    ]
    
    for subchapter in subchapters:
        conn.query("""
            MERGE (sc:SubChapter {id: $id})
            SET sc.number = $number,
                sc.title = $title
            WITH sc
            MATCH (c:Chapter {id: $chapter_id})
            MERGE (c)-[:HAS_SUBCHAPTER]->(sc)
        """, subchapter)
        print(f"  ✓ Created SubChapter {subchapter['number']}: {subchapter['title']}")
    
    # Step 4: Create Sections and Compliance Items
    # Example: Chapter 2A - Eligibility Requirements
    
    sections = [
        {
            'id': 'ICDR_SEC_6',
            'number': '6',
            'title': 'Eligibility for public issue',
            'text': 'An issuer shall be eligible to make a public issue only if it satisfies the following conditions...',
            'subchapter_id': 'ICDR_CH2_A'
        }
    ]
    
    for section in sections:
        conn.query("""
            MERGE (s:Section {id: $id})
            SET s.number = $number,
                s.title = $title,
                s.text = $text
            WITH s
            MATCH (sc:SubChapter {id: $subchapter_id})
            MERGE (sc)-[:HAS_SECTION]->(s)
        """, section)
        print(f"    ✓ Created Section {section['number']}: {section['title']}")
    
    # Step 5: Create Compliance Items (Requirements)
    compliance_items = [
        {
            'id': generate_id(),
            'requirement': 'The issuer must have net tangible assets of at least ₹3 crores in each of the preceding 3 full years',
            'mandatory': True,
            'section_id': 'ICDR_SEC_6',
            'category': 'Financial'
        },
        {
            'id': generate_id(),
            'requirement': 'The issuer must have a track record of distributable profits for at least 3 out of immediately preceding 5 years',
            'mandatory': True,
            'section_id': 'ICDR_SEC_6',
            'category': 'Financial'
        },
        {
            'id': generate_id(),
            'requirement': 'The issuer must have a minimum average pre-tax operating profit of ₹15 crores during 3 most profitable years out of immediately preceding 5 years',
            'mandatory': True,
            'section_id': 'ICDR_SEC_6',
            'category': 'Financial'
        },
        {
            'id': generate_id(),
            'requirement': 'The issuer must have net worth of at least ₹1 crore in each of the preceding 3 full years',
            'mandatory': True,
            'section_id': 'ICDR_SEC_6',
            'category': 'Financial'
        },
        {
            'id': generate_id(),
            'requirement': 'The issuer must disclose all material contracts and documents',
            'mandatory': True,
            'section_id': 'ICDR_SEC_6',
            'category': 'Disclosure'
        },
        {
            'id': generate_id(),
            'requirement': 'The prospectus must contain details of promoter shareholding pattern',
            'mandatory': True,
            'section_id': 'ICDR_SEC_6',
            'category': 'Disclosure'
        },
        {
            'id': generate_id(),
            'requirement': 'Risk factors must be prominently disclosed in the offer document',
            'mandatory': True,
            'section_id': 'ICDR_SEC_6',
            'category': 'Disclosure'
        },
        {
            'id': generate_id(),
            'requirement': 'Details of all pending litigation must be disclosed',
            'mandatory': True,
            'section_id': 'ICDR_SEC_6',
            'category': 'Legal'
        },
        {
            'id': generate_id(),
            'requirement': 'Financial statements for the last 3 years must be included',
            'mandatory': True,
            'section_id': 'ICDR_SEC_6',
            'category': 'Financial'
        },
        {
            'id': generate_id(),
            'requirement': 'Objects of the issue must be clearly stated',
            'mandatory': True,
            'section_id': 'ICDR_SEC_6',
            'category': 'Disclosure'
        },
        {
            'id': generate_id(),
            'requirement': 'Details of underwriting arrangements must be provided',
            'mandatory': False,
            'section_id': 'ICDR_SEC_6',
            'category': 'Procedure'
        },
        {
            'id': generate_id(),
            'requirement': 'Details of previous issues and their utilization must be disclosed',
            'mandatory': True,
            'section_id': 'ICDR_SEC_6',
            'category': 'Financial'
        }
    ]
    
    for item in compliance_items:
        conn.query("""
            MERGE (ci:ComplianceItem {id: $id})
            SET ci.requirement = $requirement,
                ci.mandatory = $mandatory,
                ci.category = $category
            WITH ci
            MATCH (s:Section {id: $section_id})
            MERGE (s)-[:HAS_ITEM]->(ci)
        """, item)
    
    print(f"    ✓ Created {len(compliance_items)} Compliance Items")
    
    print("\n✅ ICDR Regulations ingestion complete!")
    
    # Verify data
    result = conn.query("""
        MATCH (r:Regulation)-[:HAS_CHAPTER]->(c:Chapter)-[:HAS_SUBCHAPTER*0..1]->(sc)
              -[:HAS_SECTION]->(s:Section)-[:HAS_ITEM]->(ci:ComplianceItem)
        RETURN count(ci) as total_items
    """)
    
    print(f"✅ Total compliance items in graph: {result[0]['total_items']}")

def ingest_companies_act():
    """Ingest Companies Act, 2013 structure"""
    
    conn = get_neo4j_connection()
    
    print("\n🚀 Starting Companies Act ingestion...")
    
    # Create Regulation
    regulation_id = "COMPANIES_ACT_2013"
    conn.query("""
        MERGE (r:Regulation {id: $id})
        SET r.name = $name,
            r.type = $type,
            r.year = $year,
            r.description = $description
    """, {
        'id': regulation_id,
        'name': 'COMPANIES_ACT',
        'type': 'Act of Parliament',
        'year': 2013,
        'description': 'The Companies Act, 2013'
    })
    
    print("✓ Created Regulation: Companies Act, 2013")
    
    # Create sample chapters
    chapters = [
        {
            'id': 'CA_CH1',
            'number': '1',
            'title': 'Preliminary',
            'description': 'Short title, commencement, and definitions'
        },
        {
            'id': 'CA_CH2',
            'number': '2',
            'title': 'Incorporation of Company and Matters Incidental Thereto',
            'description': 'Company registration and incorporation'
        },
        {
            'id': 'CA_CH3',
            'number': '3',
            'title': 'Prospectus and Allotment of Securities',
            'description': 'Requirements for prospectus and securities allotment'
        },
        {
            'id': 'CA_CH4',
            'number': '4',
            'title': 'Share Capital and Debentures',
            'description': 'Provisions related to share capital'
        }
    ]
    
    for chapter in chapters:
        conn.query("""
            MERGE (c:Chapter {id: $id})
            SET c.number = $number,
                c.title = $title,
                c.description = $description
            WITH c
            MATCH (r:Regulation {id: $reg_id})
            MERGE (r)-[:HAS_CHAPTER]->(c)
        """, {
            'id': chapter['id'],
            'number': chapter['number'],
            'title': chapter['title'],
            'description': chapter['description'],
            'reg_id': regulation_id
        })
        print(f"✓ Created Chapter {chapter['number']}: {chapter['title']}")
    
    print("\n✅ Companies Act ingestion complete!")

if __name__ == "__main__":
    print("=" * 60)
    print("LEGAL DATA INGESTION SCRIPT")
    print("=" * 60)
    
    # Ingest both regulations
    ingest_icdr_regulations()
    ingest_companies_act()
    
    print("\n" + "=" * 60)
    print("✅ ALL DATA INGESTED SUCCESSFULLY!")
    print("=" * 60)
    
    # Final stats
    conn = get_neo4j_connection()
    
    stats = conn.query("""
        MATCH (r:Regulation) WITH count(r) as regs
        MATCH (c:Chapter) WITH regs, count(c) as chapters
        MATCH (sc:SubChapter) WITH regs, chapters, count(sc) as subchapters
        MATCH (s:Section) WITH regs, chapters, subchapters, count(s) as sections
        MATCH (ci:ComplianceItem) WITH regs, chapters, subchapters, sections, count(ci) as items
        RETURN regs, chapters, subchapters, sections, items
    """)
    
    print("\nGraph Statistics:")
    print(f"  Regulations: {stats[0]['regs']}")
    print(f"  Chapters: {stats[0]['chapters']}")
    print(f"  SubChapters: {stats[0]['subchapters']}")
    print(f"  Sections: {stats[0]['sections']}")
    print(f"  Compliance Items: {stats[0]['items']}")
    print("\n🎉 Ready for compliance checking!")