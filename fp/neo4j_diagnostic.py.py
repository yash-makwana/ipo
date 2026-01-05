# neo4j_diagnostic.py
"""
Neo4j Diagnostic Script
Check what's actually in the database
"""
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv('.env-local')

NEO4J_URI = os.environ.get('NEO4J_URI')
NEO4J_USER = os.environ.get('NEO4J_USER')
NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD')

print("="*80)
print("🔍 NEO4J DATABASE DIAGNOSTIC")
print("="*80)

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

try:
    with driver.session() as session:
        # Check 1: What node labels exist?
        print("\n1. NODE LABELS IN DATABASE:")
        result = session.run("CALL db.labels()")
        labels = [record[0] for record in result]
        print(f"   Found labels: {labels}")
        
        # Check 2: Count nodes by label
        print("\n2. NODE COUNTS:")
        for label in labels:
            result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
            count = result.single()['count']
            print(f"   {label}: {count} nodes")
        
        # Check 3: Sample Obligation nodes (if they exist)
        print("\n3. SAMPLE OBLIGATION NODES:")
        result = session.run("""
            MATCH (o:Obligation)
            RETURN o
            LIMIT 3
        """)
        
        obligations = list(result)
        if obligations:
            for i, record in enumerate(obligations, 1):
                node = record['o']
                print(f"\n   Obligation {i}:")
                print(f"      Properties: {list(node.keys())}")
                print(f"      regulation: {node.get('regulation')}")
                print(f"      chapter: {node.get('chapter')}")
                print(f"      section: {node.get('section')}")
                print(f"      has_embedding: {node.get('embedding') is not None}")
                if node.get('requirement_text'):
                    print(f"      text: {node.get('requirement_text')[:80]}...")
        else:
            print("   ❌ No Obligation nodes found!")
        
        # Check 4: Sample LegalChunk nodes (if they exist)
        print("\n4. SAMPLE LEGALCHUNK NODES:")
        result = session.run("""
            MATCH (c:LegalChunk)
            RETURN c
            LIMIT 3
        """)
        
        chunks = list(result)
        if chunks:
            for i, record in enumerate(chunks, 1):
                node = record['c']
                print(f"\n   LegalChunk {i}:")
                print(f"      Properties: {list(node.keys())}")
                print(f"      source_type: {node.get('source_type')}")
                print(f"      regulation_number: {node.get('regulation_number')}")
                print(f"      section_number: {node.get('section_number')}")
                print(f"      has_embedding: {node.get('embedding') is not None}")
                if node.get('text'):
                    print(f"      text: {node.get('text')[:80]}...")
        else:
            print("   ℹ️  No LegalChunk nodes found")
        
        # Check 5: What properties exist on Obligation nodes?
        print("\n5. OBLIGATION NODE SCHEMA:")
        result = session.run("""
            MATCH (o:Obligation)
            WITH o LIMIT 1
            RETURN keys(o) as properties
        """)
        record = result.single()
        if record:
            properties = record['properties']
            print(f"   Properties: {properties}")
        else:
            print("   ❌ No Obligation nodes to inspect")
        
        # Check 6: Unique values for regulation field
        print("\n6. UNIQUE REGULATION VALUES:")
        result = session.run("""
            MATCH (o:Obligation)
            RETURN DISTINCT o.regulation as regulation, count(o) as count
        """)
        for record in result:
            print(f"   '{record['regulation']}': {record['count']} obligations")
        
        # Check 7: Unique chapter values
        print("\n7. UNIQUE CHAPTER VALUES:")
        result = session.run("""
            MATCH (o:Obligation)
            WHERE o.chapter IS NOT NULL
            RETURN DISTINCT o.chapter as chapter, count(o) as count
            LIMIT 10
        """)
        chapters = list(result)
        if chapters:
            for record in chapters:
                print(f"   '{record['chapter']}': {record['count']} obligations")
        else:
            print("   ⚠️  No chapters found")
        
        # Check 8: Unique section values
        print("\n8. UNIQUE SECTION VALUES:")
        result = session.run("""
            MATCH (o:Obligation)
            WHERE o.section IS NOT NULL
            RETURN DISTINCT o.section as section, count(o) as count
            LIMIT 10
        """)
        sections = list(result)
        if sections:
            for record in sections:
                print(f"   '{record['section']}': {record['count']} obligations")
        else:
            print("   ⚠️  No sections found")
        
        # Check 9: Embedding dimensions
        print("\n9. EMBEDDING INFO:")
        result = session.run("""
            MATCH (o:Obligation)
            WHERE o.embedding IS NOT NULL
            WITH o LIMIT 1
            RETURN size(o.embedding) as embedding_dim
        """)
        record = result.single()
        if record:
            print(f"   Embedding dimension: {record['embedding_dim']}")
        else:
            print("   ❌ No embeddings found on Obligation nodes")

finally:
    driver.close()

print("\n" + "="*80)
print("✅ DIAGNOSTIC COMPLETE")
print("="*80)# neo4j_diagnostic.py
"""
Neo4j Diagnostic Script
Check what's actually in the database
"""
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv('.env-local')

NEO4J_URI = os.environ.get('NEO4J_URI')
NEO4J_USER = os.environ.get('NEO4J_USER')
NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD')

print("="*80)
print("🔍 NEO4J DATABASE DIAGNOSTIC")
print("="*80)

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

try:
    with driver.session() as session:
        # Check 1: What node labels exist?
        print("\n1. NODE LABELS IN DATABASE:")
        result = session.run("CALL db.labels()")
        labels = [record[0] for record in result]
        print(f"   Found labels: {labels}")
        
        # Check 2: Count nodes by label
        print("\n2. NODE COUNTS:")
        for label in labels:
            result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
            count = result.single()['count']
            print(f"   {label}: {count} nodes")
        
        # Check 3: Sample Obligation nodes (if they exist)
        print("\n3. SAMPLE OBLIGATION NODES:")
        result = session.run("""
            MATCH (o:Obligation)
            RETURN o
            LIMIT 3
        """)
        
        obligations = list(result)
        if obligations:
            for i, record in enumerate(obligations, 1):
                node = record['o']
                print(f"\n   Obligation {i}:")
                print(f"      Properties: {list(node.keys())}")
                print(f"      regulation: {node.get('regulation')}")
                print(f"      chapter: {node.get('chapter')}")
                print(f"      section: {node.get('section')}")
                print(f"      has_embedding: {node.get('embedding') is not None}")
                if node.get('requirement_text'):
                    print(f"      text: {node.get('requirement_text')[:80]}...")
        else:
            print("   ❌ No Obligation nodes found!")
        
        # Check 4: Sample LegalChunk nodes (if they exist)
        print("\n4. SAMPLE LEGALCHUNK NODES:")
        result = session.run("""
            MATCH (c:LegalChunk)
            RETURN c
            LIMIT 3
        """)
        
        chunks = list(result)
        if chunks:
            for i, record in enumerate(chunks, 1):
                node = record['c']
                print(f"\n   LegalChunk {i}:")
                print(f"      Properties: {list(node.keys())}")
                print(f"      source_type: {node.get('source_type')}")
                print(f"      regulation_number: {node.get('regulation_number')}")
                print(f"      section_number: {node.get('section_number')}")
                print(f"      has_embedding: {node.get('embedding') is not None}")
                if node.get('text'):
                    print(f"      text: {node.get('text')[:80]}...")
        else:
            print("   ℹ️  No LegalChunk nodes found")
        
        # Check 5: What properties exist on Obligation nodes?
        print("\n5. OBLIGATION NODE SCHEMA:")
        result = session.run("""
            MATCH (o:Obligation)
            WITH o LIMIT 1
            RETURN keys(o) as properties
        """)
        record = result.single()
        if record:
            properties = record['properties']
            print(f"   Properties: {properties}")
        else:
            print("   ❌ No Obligation nodes to inspect")
        
        # Check 6: Unique values for regulation field
        print("\n6. UNIQUE REGULATION VALUES:")
        result = session.run("""
            MATCH (o:Obligation)
            RETURN DISTINCT o.regulation as regulation, count(o) as count
        """)
        for record in result:
            print(f"   '{record['regulation']}': {record['count']} obligations")
        
        # Check 7: Unique chapter values
        print("\n7. UNIQUE CHAPTER VALUES:")
        result = session.run("""
            MATCH (o:Obligation)
            WHERE o.chapter IS NOT NULL
            RETURN DISTINCT o.chapter as chapter, count(o) as count
            LIMIT 10
        """)
        chapters = list(result)
        if chapters:
            for record in chapters:
                print(f"   '{record['chapter']}': {record['count']} obligations")
        else:
            print("   ⚠️  No chapters found")
        
        # Check 8: Unique section values
        print("\n8. UNIQUE SECTION VALUES:")
        result = session.run("""
            MATCH (o:Obligation)
            WHERE o.section IS NOT NULL
            RETURN DISTINCT o.section as section, count(o) as count
            LIMIT 10
        """)
        sections = list(result)
        if sections:
            for record in sections:
                print(f"   '{record['section']}': {record['count']} obligations")
        else:
            print("   ⚠️  No sections found")
        
        # Check 9: Embedding dimensions
        print("\n9. EMBEDDING INFO:")
        result = session.run("""
            MATCH (o:Obligation)
            WHERE o.embedding IS NOT NULL
            WITH o LIMIT 1
            RETURN size(o.embedding) as embedding_dim
        """)
        record = result.single()
        if record:
            print(f"   Embedding dimension: {record['embedding_dim']}")
        else:
            print("   ❌ No embeddings found on Obligation nodes")

finally:
    driver.close()

print("\n" + "="*80)
print("✅ DIAGNOSTIC COMPLETE")
print("="*80)