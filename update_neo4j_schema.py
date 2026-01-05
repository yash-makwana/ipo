"""
Update Neo4j Schema for Forensic Architecture
==============================================
Creates Issue nodes and links them to Regulations
"""

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

# Import checklist - adjust path if needed
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from data.checklists import NSE_ISSUES
except ImportError:
    try:
        from data.checklists import NSE_ISSUES
    except ImportError:
        print("❌ Could not import NSE_ISSUES from checklists")
        print("   Make sure checklists.py is in data/ or current directory")
        sys.exit(1)

load_dotenv('.env-local')

NEO4J_URI = os.getenv('NEO4J_URI')
NEO4J_USER = os.getenv('NEO4J_USER')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')


def create_issue_nodes():
    """Create Issue nodes linked to Regulations"""
    
    if not NEO4J_URI or not NEO4J_USER or not NEO4J_PASSWORD:
        print("❌ Neo4j credentials not found in .env-local")
        print("   Required: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD")
        return
    
    print("="*80)
    print("🔧 UPDATING NEO4J SCHEMA")
    print("="*80)
    
    driver = GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USER, NEO4J_PASSWORD)
    )
    
    try:
        with driver.session() as session:
            # Step 1: Create Issue nodes
            print(f"\n📝 Creating {len(NSE_ISSUES)} Issue nodes...")
            
            for i, issue in enumerate(NSE_ISSUES, 1):
                issue_id = issue['id']
                severity = issue.get('severity', 'Material')
                category = issue.get('category', 'Operational')
                
                session.run("""
                    MERGE (i:Issue {id: $issue_id})
                    SET i.severity = $severity,
                        i.category = $category,
                        i.updated = datetime()
                """, issue_id=issue_id, severity=severity, category=category)
                
                if i % 20 == 0:
                    print(f"   Progress: {i}/{len(NSE_ISSUES)}")
            
            print(f"   ✅ Created/Updated {len(NSE_ISSUES)} Issue nodes")
            
            # Step 2: Link to existing Regulations
            print(f"\n🔗 Linking Issues to Regulations...")
            
            links_created = 0
            
            for issue in NSE_ISSUES:
                issue_id = issue['id']
                
                # Extract keywords from issue ID
                keywords = issue_id.lower().replace('_', ' ').split()
                
                # Skip if no meaningful keywords
                if len(keywords) < 2:
                    continue
                
                # Try to find matching regulation
                try:
                    result = session.run("""
                        MATCH (i:Issue {id: $issue_id})
                        MATCH (r:Regulation)
                        WHERE toLower(r.requirement_text) CONTAINS $keyword1
                           OR toLower(r.requirement_text) CONTAINS $keyword2
                           OR toLower(r.source_clause) CONTAINS $keyword1
                        WITH i, r LIMIT 1
                        MERGE (i)-[:LINKED_TO]->(r)
                        RETURN count(r) as links
                    """, 
                    issue_id=issue_id,
                    keyword1=keywords[0],
                    keyword2=keywords[1]
                    )
                    
                    record = result.single()
                    if record and record['links'] > 0:
                        links_created += 1
                        if links_created % 10 == 0:
                            print(f"   Progress: {links_created} links created")
                
                except Exception as e:
                    # Skip if linking fails for this issue
                    continue
            
            print(f"   ✅ Created {links_created} Issue-Regulation links")
            
            # Step 3: Verify
            print(f"\n🔍 Verification...")
            
            result = session.run("""
                MATCH (i:Issue)
                RETURN count(i) as total_issues
            """)
            total_issues = result.single()['total_issues']
            
            result = session.run("""
                MATCH (i:Issue)-[:LINKED_TO]->(r:Regulation)
                RETURN count(i) as linked_issues
            """)
            linked_issues = result.single()['linked_issues']
            
            print(f"   Total Issue nodes: {total_issues}")
            print(f"   Linked to Regulations: {linked_issues}")
            print(f"   Unlinked: {total_issues - linked_issues}")
            
            if linked_issues < total_issues * 0.5:
                print(f"\n   ⚠️  Warning: Less than 50% of issues are linked")
                print(f"   This is okay - fallback mechanism will handle unlinked issues")
    
    except Exception as e:
        print(f"\n❌ Error updating Neo4j: {e}")
        import traceback
        traceback.print_exc()
        return
    
    finally:
        driver.close()
    
    print(f"\n{'='*80}")
    print(f"✅ NEO4J SCHEMA UPDATE COMPLETE")
    print(f"{'='*80}")
    print(f"\n📋 Summary:")
    print(f"   - Issue nodes created: {len(NSE_ISSUES)}")
    print(f"   - Regulation links: {links_created}")
    print(f"   - Coverage: {(linked_issues/total_issues)*100:.1f}%")
    print(f"\n💡 Note: Unlinked issues will use keyword-based fallback")


if __name__ == "__main__":
    create_issue_nodes()