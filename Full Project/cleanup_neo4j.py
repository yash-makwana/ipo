#!/usr/bin/env python3
"""
NEO4J DATABASE CLEANUP
=====================
Clears all legal data from Neo4j before fresh ingestion.
"""

from db_config import get_neo4j_connection

def cleanup_neo4j():
    """Delete all nodes and relationships."""
    
    print("=" * 80)
    print("🗑️  NEO4J DATABASE CLEANUP")
    print("=" * 80)
    
    try:
        driver = get_neo4j_connection()
        print("✅ Connected to Neo4j\n")
        
        with driver.session() as session:
            # Count existing data
            print("📊 Current database state:")
            
            counts = {}
            for label in ['Regulation', 'Chapter', 'Section', 'Obligation', 'Requirement']:
                result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
                count = result.single()['count']
                counts[label] = count
                print(f"   {label}: {count}")
            
            total = sum(counts.values())
            
            if total == 0:
                print("\n✅ Database is already empty!")
                return
            
            # Confirm deletion
            print(f"\n⚠️  WARNING: This will delete {total} nodes!")
            response = input("Type 'DELETE' to confirm: ")
            
            if response != 'DELETE':
                print("\n❌ Cleanup cancelled.")
                return
            
            print("\n🗑️  Deleting all data...")
            
            # Delete everything
            session.run("MATCH (n) DETACH DELETE n")
            
            # Verify deletion
            result = session.run("MATCH (n) RETURN count(n) as count")
            remaining = result.single()['count']
            
            if remaining == 0:
                print("✅ All data deleted successfully!")
                print("\n💡 You can now run fresh ingestion:")
                print("   python ingest_legal_data_obligation_based.py --pdf-dir ./legal_pdfs --max-chapters 100")
            else:
                print(f"⚠️  Warning: {remaining} nodes still remain")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print("\n" + "=" * 80)
    return 0

if __name__ == "__main__":
    exit(cleanup_neo4j())