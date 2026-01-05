# check_relationships.py
"""Check what relationships exist in Neo4j"""
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv('.env-local')

driver = GraphDatabase.driver(
    os.environ.get('NEO4J_URI'),
    auth=(os.environ.get('NEO4J_USER'), os.environ.get('NEO4J_PASSWORD'))
)

print("="*80)
print("🔍 CHECKING NEO4J RELATIONSHIPS")
print("="*80)

with driver.session() as session:
    # Check relationship types
    print("\n1. RELATIONSHIP TYPES:")
    result = session.run("CALL db.relationshipTypes()")
    rel_types = [record[0] for record in result]
    print(f"   Found: {rel_types}")
    
    # Check how Obligations connect to Chapters
    print("\n2. OBLIGATION → CHAPTER CONNECTIONS:")
    result = session.run("""
        MATCH (o:Obligation)-[r]->(c:Chapter)
        RETURN type(r) as rel_type, count(*) as count
    """)
    connections = list(result)
    if connections:
        for record in connections:
            print(f"   {record['rel_type']}: {record['count']} connections")
    else:
        print("   ❌ No direct connections found")
    
    # Check reverse direction
    print("\n3. CHAPTER → OBLIGATION CONNECTIONS:")
    result = session.run("""
        MATCH (c:Chapter)-[r]->(o:Obligation)
        RETURN type(r) as rel_type, count(*) as count
    """)
    connections = list(result)
    if connections:
        for record in connections:
            print(f"   {record['rel_type']}: {record['count']} connections")
    else:
        print("   ❌ No connections found")
    
    # Check what Chapter nodes look like
    print("\n4. SAMPLE CHAPTER NODES:")
    result = session.run("MATCH (c:Chapter) RETURN c LIMIT 3")
    for i, record in enumerate(result, 1):
        chapter = record['c']
        print(f"\n   Chapter {i}:")
        print(f"      Properties: {dict(chapter)}")
    
    # Check if chapter info is in source_clause
    print("\n5. SAMPLE SOURCE_CLAUSE VALUES:")
    result = session.run("""
        MATCH (o:Obligation)
        WHERE o.source_clause IS NOT NULL
        RETURN DISTINCT o.source_clause as clause
        LIMIT 10
    """)
    for record in result:
        print(f"   - {record['clause']}")

driver.close()
print("\n" + "="*80)