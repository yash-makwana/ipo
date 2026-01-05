# ingest_legal_data_DRHP_focused.py
"""
DRHP-Focused Legal Data Ingestion
Extracts requirements specifically relevant for IPO compliance checking
"""

from google.cloud import storage
from vertexai.generative_models import GenerativeModel
from google.cloud import aiplatform
from db_config import get_neo4j_connection
import json
import os
import uuid
import time
import re
from typing import List, Dict
import PyPDF2
from io import BytesIO

PROJECT_ID = os.environ.get('GCP_PROJECT')

# ============================================================================
# CURATED REQUIREMENTS FOR DRHP COMPLIANCE
# ============================================================================

DRHP_FOCUSED_REQUIREMENTS = {
    "ICDR": {
        "Chapter_II": {
            "number": "II",
            "title": "GENERAL CONDITIONS",
            "sections": [
                {
                    "number": "4",
                    "title": "Filing of offer document",
                    "requirements": [
                        {
                            "text": "Draft offer document shall be filed with the Board along with fees specified in Schedule III",
                            "category": "Procedural",
                            "mandatory": True,
                            "applies_to": ["public_issue", "rights_issue"]
                        },
                        {
                            "text": "Draft offer document shall be filed with stock exchanges",
                            "category": "Procedural",
                            "mandatory": True,
                            "applies_to": ["public_issue"]
                        }
                    ]
                },
                {
                    "number": "5",
                    "title": "Validity of observations of the Board",
                    "requirements": [
                        {
                            "text": "Issuer shall file updated draft red herring prospectus-I with the Board within sixteen months from the date of issuance of observations",
                            "category": "Timeline",
                            "mandatory": True,
                            "applies_to": ["public_issue"]
                        },
                        {
                            "text": "Public issue may be opened within eighteen months from the date of issuance of observations by the Board",
                            "category": "Timeline",
                            "mandatory": True,
                            "applies_to": ["public_issue"]
                        }
                    ]
                },
                {
                    "number": "6",
                    "title": "General disclosures in offer document",
                    "requirements": [
                        {
                            "text": "Offer document shall contain complete, true and adequate disclosure of all material facts",
                            "category": "Disclosure",
                            "mandatory": True,
                            "applies_to": ["all_issues"]
                        },
                        {
                            "text": "Risk factors shall be disclosed prominently in the offer document",
                            "category": "Risk Disclosure",
                            "mandatory": True,
                            "applies_to": ["all_issues"]
                        },
                        {
                            "text": "Top ten risk factors shall be disclosed on the cover page",
                            "category": "Risk Disclosure",
                            "mandatory": True,
                            "applies_to": ["public_issue"]
                        }
                    ]
                }
            ]
        }
    },
    
    "COMPANIES_ACT": {
        "Section_26": {
            "number": "26",
            "title": "Matters to be stated in prospectus",
            "chapter": "III",
            "requirements": [
                {
                    "text": "Prospectus shall state the main objects of the company and present objects",
                    "category": "Business Disclosure",
                    "mandatory": True,
                    "applies_to": ["public_issue"]
                },
                {
                    "text": "Prospectus shall disclose details of directors including their appointment and remuneration",
                    "category": "Management Disclosure",
                    "mandatory": True,
                    "applies_to": ["public_issue"]
                },
                {
                    "text": "Prospectus shall contain details of promoters and promoter group",
                    "category": "Promoter Disclosure",
                    "mandatory": True,
                    "applies_to": ["public_issue"]
                },
                {
                    "text": "Prospectus shall disclose the nature and extent of interest of directors in promotion or property acquisition",
                    "category": "Related Party Disclosure",
                    "mandatory": True,
                    "applies_to": ["public_issue"]
                },
                {
                    "text": "Prospectus shall contain audited financial statements for last three financial years",
                    "category": "Financial Disclosure",
                    "mandatory": True,
                    "applies_to": ["public_issue"]
                }
            ]
        },
        
        "Section_29": {
            "number": "29",
            "title": "Expert's consent for inclusion of statement",
            "chapter": "III",
            "requirements": [
                {
                    "text": "Expert's consent shall be obtained before including their statement in prospectus",
                    "category": "Legal Compliance",
                    "mandatory": True,
                    "applies_to": ["public_issue"]
                },
                {
                    "text": "Prospectus shall contain written consent from expert regarding inclusion of their opinion",
                    "category": "Legal Compliance",
                    "mandatory": True,
                    "applies_to": ["public_issue"]
                }
            ]
        },
        
        "Section_32": {
            "number": "32",
            "title": "Variation in terms of contract or objects in prospectus",
            "chapter": "III",
            "requirements": [
                {
                    "text": "Any variation in objects for which funds are raised shall require special resolution",
                    "category": "Legal Compliance",
                    "mandatory": True,
                    "applies_to": ["public_issue"]
                }
            ]
        }
    }
}

# ============================================================================
# ENHANCED EXTRACTION FOR ADDITIONAL REQUIREMENTS
# ============================================================================

def extract_additional_requirements_from_pdf(gcs_uri, regulation_name):
    """
    Extract additional requirements from actual PDF using smart parsing
    """
    print(f"\n📄 Extracting additional requirements from {regulation_name} PDF...")
    
    try:
        storage_client = storage.Client()
        bucket_name = gcs_uri.replace('gs://', '').split('/')[0]
        blob_path = '/'.join(gcs_uri.replace('gs://', '').split('/')[1:])
        
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        pdf_content = blob.download_as_bytes()
        
        pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_content))
        
        # Extract specific chapters/sections
        if regulation_name == "ICDR":
            target_chapters = ["II", "III"]
        else:  # Companies Act
            target_chapters = ["III", "IV"]
        
        extracted_text = {}
        
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text = page.extract_text()
            
            # Look for chapter/section markers
            for chapter in target_chapters:
                if f"CHAPTER {chapter}" in text.upper() or f"Section {chapter}" in text:
                    if chapter not in extracted_text:
                        extracted_text[chapter] = ""
                    extracted_text[chapter] += text + "\n\n"
        
        print(f"   ✅ Extracted {len(extracted_text)} relevant chapters")
        
        return extracted_text
        
    except Exception as e:
        print(f"   ⚠️  Error extracting from PDF: {e}")
        return {}

def parse_additional_requirements_with_gemini(chapter_text, regulation_name, chapter_num):
    """
    Use Gemini to extract ADDITIONAL requirements from PDF text
    Focus on DRHP-relevant requirements only
    """
    print(f"   🤖 Parsing Chapter {chapter_num} with Gemini...")
    
    aiplatform.init(project=PROJECT_ID, location="us-central1")
    model = GenerativeModel("gemini-2.5-pro")
    
    if len(chapter_text) > 100000:
        chapter_text = chapter_text[:100000]
    
    prompt = f"""You are extracting IPO/DRHP compliance requirements from {regulation_name}.

Extract ONLY requirements relevant to:
- Public issue disclosures
- Risk factor disclosures
- Business description requirements
- Financial statement requirements
- Management/promoter disclosures
- Material contracts
- Legal proceedings

For Chapter {chapter_num}, extract requirements in this JSON format:

{{
  "requirements": [
    {{
      "section_number": "6",
      "section_title": "Risk factor disclosures",
      "requirement_text": "Exact requirement from document",
      "category": "Risk Disclosure|Business Disclosure|Financial Disclosure|Management Disclosure|Legal Compliance",
      "mandatory": true,
      "applies_to": ["public_issue"]
    }}
  ]
}}

RULES:
- Extract ACTUAL text from document (don't invent)
- Focus on DRHP-relevant requirements only
- Skip procedural/filing requirements (we already have those)
- Categories: Risk Disclosure, Business Disclosure, Financial Disclosure, Management Disclosure, Legal Compliance, Related Party Disclosure

Text:

{chapter_text}

Return ONLY JSON, no markdown."""

    try:
        response = model.generate_content(prompt)
        text = response.text
        
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        
        result = json.loads(text.strip())
        print(f"      ✅ Found {len(result.get('requirements', []))} additional requirements")
        return result.get('requirements', [])
        
    except Exception as e:
        print(f"      ⚠️  Gemini parsing error: {e}")
        return []

# ============================================================================
# NEO4J SCHEMA
# ============================================================================

def create_graph_schema(conn):
    """Create optimized schema"""
    print("📊 Creating graph schema...")
    
    constraints = [
        "CREATE CONSTRAINT regulation_id IF NOT EXISTS FOR (r:Regulation) REQUIRE r.id IS UNIQUE",
        "CREATE CONSTRAINT chapter_id IF NOT EXISTS FOR (c:Chapter) REQUIRE c.id IS UNIQUE",
        "CREATE CONSTRAINT section_id IF NOT EXISTS FOR (s:Section) REQUIRE s.id IS UNIQUE",
        "CREATE CONSTRAINT compliance_id IF NOT EXISTS FOR (ci:ComplianceItem) REQUIRE ci.id IS UNIQUE",
    ]
    
    for constraint in constraints:
        try:
            conn.query(constraint)
        except:
            pass
    
    indexes = [
        "CREATE INDEX regulation_name IF NOT EXISTS FOR (r:Regulation) ON (r.name)",
        "CREATE INDEX chapter_number IF NOT EXISTS FOR (c:Chapter) ON (c.number)",
        "CREATE INDEX section_number IF NOT EXISTS FOR (s:Section) ON (s.number)",
        "CREATE INDEX compliance_category IF NOT EXISTS FOR (ci:ComplianceItem) ON (ci.category)",
    ]
    
    for index in indexes:
        try:
            conn.query(index)
        except:
            pass
    
    print("   ✅ Schema ready")

# ============================================================================
# INGEST CURATED + EXTRACTED REQUIREMENTS
# ============================================================================

def ingest_requirements_to_neo4j(regulation_name, requirements_data, pdf_uri=None):
    """
    Ingest curated requirements + extracted requirements to Neo4j
    """
    print(f"\n💾 Ingesting {regulation_name} requirements...")
    
    conn = get_neo4j_connection()
    create_graph_schema(conn)
    
    # Create Regulation node
    conn.query("""
        MERGE (r:Regulation {id: $id})
        SET r.name = $name,
            r.ingested_at = timestamp()
    """, {
        'id': regulation_name,
        'name': regulation_name
    })
    
    total_requirements = 0
    
    # Process curated requirements
    for chapter_key, chapter_data in requirements_data.items():
        chapter_num = chapter_data['number']
        chapter_id = f"{regulation_name}_CH{chapter_num}"
        
        # Create Chapter
        conn.query("""
            MERGE (c:Chapter {id: $id})
            SET c.number = $number,
                c.title = $title
            WITH c
            MATCH (r:Regulation {id: $reg_id})
            MERGE (r)-[:HAS_CHAPTER]->(c)
        """, {
            'id': chapter_id,
            'number': chapter_num,
            'title': chapter_data['title'],
            'reg_id': regulation_name
        })
        
        print(f"   📖 Chapter {chapter_num}: {chapter_data['title']}")
        
        # Process sections
        for section_data in chapter_data.get('sections', []):
            section_num = section_data['number']
            section_id = f"{chapter_id}_SEC{section_num}"
            
            # Create Section
            conn.query("""
                MERGE (s:Section {id: $id})
                SET s.number = $number,
                    s.title = $title
                WITH s
                MATCH (c:Chapter {id: $chapter_id})
                MERGE (c)-[:HAS_SECTION]->(s)
            """, {
                'id': section_id,
                'number': str(section_num),
                'title': section_data['title'],
                'chapter_id': chapter_id
            })
            
            # Create compliance items
            for req in section_data.get('requirements', []):
                item_id = f"CMP_{uuid.uuid4().hex[:8]}"
                
                conn.query("""
                    MERGE (ci:ComplianceItem {id: $id})
                    SET ci.requirement_text = $text,
                        ci.mandatory = $mandatory,
                        ci.category = $category,
                        ci.applies_to = $applies_to
                    WITH ci
                    MATCH (s:Section {id: $section_id})
                    MERGE (s)-[:REQUIRES]->(ci)
                """, {
                    'id': item_id,
                    'text': req['text'],
                    'mandatory': req.get('mandatory', True),
                    'category': req.get('category', 'General'),
                    'applies_to': req.get('applies_to', ['all_issues']),
                    'section_id': section_id
                })
                
                total_requirements += 1
            
            print(f"      ✅ Section {section_num}: {len(section_data.get('requirements', []))} requirements")
    
    # Extract additional requirements from PDF if provided
    if pdf_uri:
        additional_reqs = extract_and_parse_pdf(pdf_uri, regulation_name, conn)
        total_requirements += additional_reqs
    
    print(f"\n   ✅ Total requirements ingested: {total_requirements}")
    return total_requirements

def extract_and_parse_pdf(pdf_uri, regulation_name, conn):
    """
    Extract additional requirements from PDF and add to Neo4j
    """
    print(f"\n📄 Extracting additional requirements from PDF...")
    
    extracted_chapters = extract_additional_requirements_from_pdf(pdf_uri, regulation_name)
    
    additional_count = 0
    
    for chapter_num, chapter_text in extracted_chapters.items():
        additional_reqs = parse_additional_requirements_with_gemini(
            chapter_text,
            regulation_name,
            chapter_num
        )
        
        chapter_id = f"{regulation_name}_CH{chapter_num}"
        
        for req_data in additional_reqs:
            section_num = req_data.get('section_number', '99')
            section_title = req_data.get('section_title', 'Additional Requirements')
            section_id = f"{chapter_id}_SEC{section_num}"
            
            # Create section if doesn't exist
            conn.query("""
                MERGE (s:Section {id: $id})
                SET s.number = $number,
                    s.title = $title
                WITH s
                MATCH (c:Chapter {id: $chapter_id})
                MERGE (c)-[:HAS_SECTION]->(s)
            """, {
                'id': section_id,
                'number': str(section_num),
                'title': section_title,
                'chapter_id': chapter_id
            })
            
            # Create compliance item
            item_id = f"CMP_{uuid.uuid4().hex[:8]}"
            
            conn.query("""
                MERGE (ci:ComplianceItem {id: $id})
                SET ci.requirement_text = $text,
                    ci.mandatory = $mandatory,
                    ci.category = $category,
                    ci.applies_to = $applies_to
                WITH ci
                MATCH (s:Section {id: $section_id})
                MERGE (s)-[:REQUIRES]->(ci)
            """, {
                'id': item_id,
                'text': req_data['requirement_text'],
                'mandatory': req_data.get('mandatory', True),
                'category': req_data.get('category', 'General'),
                'applies_to': req_data.get('applies_to', ['all_issues']),
                'section_id': section_id
            })
            
            additional_count += 1
    
    print(f"   ✅ Added {additional_count} requirements from PDF")
    return additional_count

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """
    Main ingestion pipeline
    """
    print("=" * 80)
    print("🚀 DRHP-FOCUSED LEGAL DATA INGESTION")
    print("=" * 80)
    
    BUCKET_NAME = "ipo-compliance-system-legal-docs/legal-docs"
    
    # Ingest ICDR (curated + extracted)
    print("\n📋 ICDR REGULATIONS")
    print("-" * 80)
    
    icdr_count = ingest_requirements_to_neo4j(
        regulation_name="ICDR",
        requirements_data=DRHP_FOCUSED_REQUIREMENTS["ICDR"],
        pdf_uri=f"gs://{BUCKET_NAME}/ICDR_Regulations_2018.pdf"  # Your uploaded SEBI PDF
    )
    
    time.sleep(3)
    
    # Ingest Companies Act (curated + extracted)
    print("\n📋 COMPANIES ACT 2013")
    print("-" * 80)
    
    companies_count = ingest_requirements_to_neo4j(
        regulation_name="COMPANIES_ACT",
        requirements_data=DRHP_FOCUSED_REQUIREMENTS["COMPANIES_ACT"],
        pdf_uri=f"gs://{BUCKET_NAME}/Companies_Act_2013.pdf"  # Your uploaded Companies Act PDF
    )
    
    print("\n" + "=" * 80)
    print("✅ INGESTION COMPLETE")
    print(f"   ICDR Requirements: {icdr_count}")
    print(f"   Companies Act Requirements: {companies_count}")
    print(f"   Total: {icdr_count + companies_count}")
    print("=" * 80)

if __name__ == "__main__":
    main()