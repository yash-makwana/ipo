from db_config import get_neo4j_connection

def create_graph_schema():
    """Create the Neo4j graph schema for legal compliance"""
    
    conn = get_neo4j_connection()
    
    # Create constraints (ensures uniqueness)
    constraints = [
        "CREATE CONSTRAINT regulation_id IF NOT EXISTS FOR (r:Regulation) REQUIRE r.id IS UNIQUE",
        "CREATE CONSTRAINT chapter_id IF NOT EXISTS FOR (c:Chapter) REQUIRE c.id IS UNIQUE",
        "CREATE CONSTRAINT subchapter_id IF NOT EXISTS FOR (sc:SubChapter) REQUIRE sc.id IS UNIQUE",
        "CREATE CONSTRAINT section_id IF NOT EXISTS FOR (s:Section) REQUIRE s.id IS UNIQUE",
        "CREATE CONSTRAINT item_id IF NOT EXISTS FOR (ci:ComplianceItem) REQUIRE ci.id IS UNIQUE",
    ]
    
    print("Creating constraints...")
    for constraint in constraints:
        try:
            conn.query(constraint)
            print(f"✓ {constraint.split()[2]}")
        except Exception as e:
            print(f"✗ {str(e)}")
    
    # Create indexes (improves query performance)
    indexes = [
        "CREATE INDEX regulation_name IF NOT EXISTS FOR (r:Regulation) ON (r.name)",
        "CREATE INDEX chapter_number IF NOT EXISTS FOR (c:Chapter) ON (c.number)",
    ]
    
    print("\nCreating indexes...")
    for index in indexes:
        try:
            conn.query(index)
            print(f"✓ {index.split()[2]}")
        except Exception as e:
            print(f"✗ {str(e)}")
    
    print("\n✅ Schema created successfully!")

if __name__ == "__main__":
    create_graph_schema()
