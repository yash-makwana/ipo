# Add this to your main.py

from db_config import get_neo4j_connection

@app.route('/api/regulations/<reg_id>/chapters', methods=['GET'])
def get_chapters(reg_id):
    """Get REAL chapters from Neo4j"""
    try:
        conn = get_neo4j_connection()
        
        result = conn.query("""
            MATCH (r:Regulation {name: $reg_id})-[:HAS_CHAPTER]->(c:Chapter)
            RETURN c.id as id, c.number as number, c.title as title, c.description as description
            ORDER BY toInteger(c.number)
        """, {'reg_id': reg_id})
        
        chapters = [dict(record) for record in result]
        
        return jsonify({'chapters': chapters})
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/regulations/<reg_id>/chapters/<chapter_id>/subchapters', methods=['GET'])
def get_subchapters(reg_id, chapter_id):
    """Get REAL subchapters from Neo4j"""
    try:
        conn = get_neo4j_connection()
        
        # Find the full chapter ID
        chapter_full_id = f"{reg_id}_CH{chapter_id}"
        
        result = conn.query("""
            MATCH (c:Chapter {id: $chapter_id})-[:HAS_SUBCHAPTER]->(sc:SubChapter)
            RETURN sc.id as id, sc.number as number, sc.title as title
            ORDER BY sc.number
        """, {'chapter_id': chapter_full_id})
        
        subchapters = [dict(record) for record in result]
        
        return jsonify({'subchapters': subchapters})
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500
