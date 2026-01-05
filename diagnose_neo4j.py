"""
Diagnose Neo4j Schema - Check what nodes/properties exist
"""

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv('.env-local')

NEO4J_URI = os.getenv('NEO4J_URI')
NEO4J_USER = os.getenv('NEO4J_USER')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')


def diagnose_schema():
    """Check what's actually in your Neo4j database"""
    
    print("="*80)
    print("🔍 NEO4J SCHEMA DIAGNOSIS")
    print("="*80)
    
    driver = GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USER, NEO4J_PASSWORD)
    )
    
    try:
        with driver.session() as session:
            # Check 1: Total nodes
            print("\n📊 Database Overview:")
            result = session.run("""
                MATCH (n)
                RETURN count(n) as total
            """)
            total = result.single()['total']
            print(f"   Total nodes in database: {total}")
            
            # Check 2: What node types exist?
            print("\n📊 Node Types (Labels):")
            result = session.run("""
                CALL db.labels()
                YIELD label
                RETURN label
                ORDER BY label
            """)
            
            all_labels = [record['label'] for record in result]
            print(f"   Found {len(all_labels)} different labels:")
            for label in all_labels:
                print(f"   - {label}")
            
            # Count nodes per label
            print("\n📊 Node Counts:")
            result = session.run("""
                MATCH (n)
                RETURN DISTINCT labels(n) as labels, count(n) as count
                ORDER BY count DESC
            """)
            
            node_types = {}
            for record in result:
                labels = record['labels']
                count = record['count']
                label = labels[0] if labels else 'Unknown'
                node_types[label] = count
                print(f"   {label}: {count} nodes")
            
            # Check 2: Sample Regulation node structure
            if 'Regulation' in node_types:
                print(f"\n📝 Sample Regulation Node:")
                result = session.run("""
                    MATCH (r:Regulation)
                    RETURN r
                    LIMIT 1
                """)
                
                record = result.single()
                if record:
                    reg = record['r']
                    print(f"   Properties available:")
                    for key in reg.keys():
                        value = reg[key]
                        if isinstance(value, str) and len(value) > 100:
                            value = value[:100] + "..."
                        print(f"   - {key}: {value}")
                else:
                    print(f"   No Regulation nodes found")
            
            # Check 3: What properties do Regulation nodes have?
            if 'Regulation' in node_types:
                print(f"\n🔑 All Properties on Regulation Nodes:")
                result = session.run("""
                    MATCH (r:Regulation)
                    UNWIND keys(r) as key
                    RETURN DISTINCT key
                    ORDER BY key
                """)
                
                properties = [record['key'] for record in result]
                for prop in properties:
                    print(f"   - {prop}")
            
            # Check 4: Sample text from regulations
            if 'Regulation' in node_types:
                print(f"\n📄 Sample Regulation Texts (first 3):")
                
                # Try different possible text fields
                text_fields = ['text', 'requirement_text', 'source_clause', 
                              'clause_text', 'content', 'description']
                
                for field in text_fields:
                    try:
                        result = session.run(f"""
                            MATCH (r:Regulation)
                            WHERE r.{field} IS NOT NULL
                            RETURN r.{field} as text
                            LIMIT 3
                        """)
                        
                        records = list(result)
                        if records:
                            print(f"\n   Field: {field} (Found {len(records)} samples)")
                            for i, record in enumerate(records, 1):
                                text = record['text']
                                if isinstance(text, str):
                                    snippet = text[:150].replace('\n', ' ')
                                    print(f"   [{i}] {snippet}...")
                            break
                    except:
                        continue
            
            # Check 5: Issue nodes (we just created)
            print(f"\n✅ Issue Nodes Created:")
            result = session.run("""
                MATCH (i:Issue)
                RETURN count(i) as count
            """)
            count = result.single()['count']
            print(f"   Total: {count}")
            
            # Sample Issue
            result = session.run("""
                MATCH (i:Issue)
                RETURN i
                LIMIT 1
            """)
            record = result.single()
            if record:
                issue = record['i']
                print(f"   Sample Issue: {issue.get('id')}")
                print(f"   Properties: {list(issue.keys())}")
            
            # Check 6: Any nodes that are NOT Issue nodes?
            print(f"\n🔍 Non-Issue Nodes:")
            result = session.run("""
                MATCH (n)
                WHERE NOT n:Issue
                RETURN DISTINCT labels(n) as labels, count(n) as count
            """)
            
            other_nodes = list(result)
            if other_nodes:
                print(f"   Found other node types:")
                for record in other_nodes:
                    print(f"   - {record['labels']}: {record['count']} nodes")
            else:
                print(f"   ❌ NO OTHER NODES FOUND")
                print(f"   Your Neo4j only has Issue nodes - no regulations!")
            
            # Check 7: Sample of ANY node that's not Issue
            print(f"\n📝 Sample Non-Issue Node (if any):")
            result = session.run("""
                MATCH (n)
                WHERE NOT n:Issue
                RETURN n, labels(n) as labels
                LIMIT 1
            """)
            
            record = result.single()
            if record:
                node = record['n']
                labels = record['labels']
                print(f"   Labels: {labels}")
                print(f"   Properties:")
                for key in node.keys():
                    value = node[key]
                    if isinstance(value, str) and len(value) > 100:
                        value = value[:100] + "..."
                    print(f"   - {key}: {value}")
            else:
                print(f"   None - database is empty except for Issue nodes")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.close()
    
    print(f"\n{'='*80}")
    print(f"💡 DIAGNOSIS COMPLETE")
    print(f"{'='*80}")


if __name__ == "__main__":
    diagnose_schema()