# graph_rag_query.py
# Query module for Graph RAG on legal knowledge base

from typing import List, Dict, Optional
from dataclasses import dataclass
from db_config import get_neo4j_connection
import json

@dataclass
class ComplianceResult:
    """Result from compliance query"""
    regulation: str
    chapter: str
    section: str
    requirement: str
    mandatory: bool
    category: str
    deadline_type: str
    applies_to: List[str]
    confidence_score: float = 0.0

class LegalGraphRAG:
    """
    Graph RAG query interface for legal compliance checking
    """
    
    def __init__(self):
        self.conn = get_neo4j_connection()
    
    # ========================================================================
    # QUERY 1: Find All Requirements for a Specific Topic
    # ========================================================================
    
    def find_requirements_by_topic(self, topic: str, regulation: Optional[str] = None) -> List[ComplianceResult]:
        """
        Find all compliance requirements related to a topic
        
        Example: "What are the prospectus requirements?"
        """
        query = """
        CALL db.index.fulltext.queryNodes('section_text', $topic)
        YIELD node as s, score
        MATCH (s:Section)<-[:HAS_SECTION]-(c:Chapter)<-[:HAS_CHAPTER]-(r:Regulation)
        MATCH (s)-[:REQUIRES]->(ci:ComplianceItem)
        WHERE ($regulation IS NULL OR r.id = $regulation)
        RETURN DISTINCT
            r.name as regulation,
            c.number as chapter_number,
            c.title as chapter_title,
            s.number as section_number,
            s.title as section_title,
            ci.requirement_text as requirement,
            ci.mandatory as mandatory,
            ci.category as category,
            ci.deadline_type as deadline_type,
            ci.applies_to as applies_to,
            score
        ORDER BY score DESC, c.number, s.number
        LIMIT 20
        """
        
        results = self.conn.query(query, {
            'topic': topic,
            'regulation': regulation
        })
        
        return [
            ComplianceResult(
                regulation=r['regulation'],
                chapter=f"{r['chapter_number']} - {r['chapter_title']}",
                section=f"{r['section_number']} - {r['section_title']}",
                requirement=r['requirement'],
                mandatory=r['mandatory'],
                category=r['category'],
                deadline_type=r['deadline_type'],
                applies_to=r['applies_to'],
                confidence_score=r['score']
            )
            for r in results
        ]
    
    # ========================================================================
    # QUERY 2: Find Requirements by Category
    # ========================================================================
    
    def find_by_category(self, category: str, mandatory_only: bool = False) -> List[Dict]:
        """
        Get all requirements of a specific category
        
        Categories: Financial, Disclosure, Procedural, Timeline, Legal
        """
        query = """
        MATCH (r:Regulation)-[:HAS_CHAPTER]->(c:Chapter)-[:HAS_SECTION]->(s:Section)-[:REQUIRES]->(ci:ComplianceItem)
        WHERE ci.category = $category
            AND ($mandatory_only = false OR ci.mandatory = true)
        RETURN 
            r.name as regulation,
            c.title as chapter,
            s.number as section_number,
            s.title as section_title,
            ci.requirement_text as requirement,
            ci.mandatory as mandatory,
            ci.deadline_type as deadline_type
        ORDER BY r.name, c.number, s.number
        """
        
        return self.conn.query(query, {
            'category': category,
            'mandatory_only': mandatory_only
        })
    
    # ========================================================================
    # QUERY 3: Get Complete Section Context
    # ========================================================================
    
    def get_section_full_context(self, section_number: str, regulation: str) -> Dict:
        """
        Get complete context for a section including all related info
        
        This is useful when you need to understand a section in depth
        """
        query = """
        MATCH (r:Regulation {id: $regulation})-[:HAS_CHAPTER]->(c:Chapter)-[:HAS_SECTION]->(s:Section {number: $section_number})
        OPTIONAL MATCH (s)-[:REQUIRES]->(ci:ComplianceItem)
        RETURN 
            r.name as regulation,
            c.number as chapter_number,
            c.title as chapter_title,
            s.number as section_number,
            s.title as section_title,
            s.full_text as full_text,
            s.summary as summary,
            collect(DISTINCT {
                requirement: ci.requirement_text,
                mandatory: ci.mandatory,
                category: ci.category,
                deadline: ci.deadline_type,
                applies_to: ci.applies_to
            }) as compliance_items
        """
        
        result = self.conn.query(query, {
            'section_number': section_number,
            'regulation': regulation
        })
        
        return result[0] if result else None
    
    # ========================================================================
    # QUERY 4: Find Conflicting Requirements
    # ========================================================================
    
    def find_potential_conflicts(self, topic: str) -> List[Dict]:
        """
        Find requirements that might conflict on the same topic
        
        Useful for identifying edge cases
        """
        query = """
        CALL db.index.fulltext.queryNodes('section_text', $topic)
        YIELD node as s, score
        MATCH (s)-[:REQUIRES]->(ci:ComplianceItem)
        WITH s, ci, score
        WHERE score > 0.5
        WITH collect({
            section: s.number,
            requirement: ci.requirement_text,
            mandatory: ci.mandatory
        }) as requirements
        WHERE size(requirements) > 1
        RETURN requirements
        """
        
        return self.conn.query(query, {'topic': topic})
    
    # ========================================================================
    # QUERY 5: Get Timeline-based Requirements
    # ========================================================================
    
    def get_timeline_requirements(self, deadline_type: str) -> List[Dict]:
        """
        Get all requirements based on timeline
        
        deadline_type: 'pre-filing', 'at-filing', 'post-approval', 'ongoing'
        """
        query = """
        MATCH (r:Regulation)-[:HAS_CHAPTER]->(c:Chapter)-[:HAS_SECTION]->(s:Section)-[:REQUIRES]->(ci:ComplianceItem)
        WHERE ci.deadline_type = $deadline_type
        RETURN 
            r.name as regulation,
            c.title as chapter,
            s.number + ': ' + s.title as section,
            ci.requirement_text as requirement,
            ci.mandatory as mandatory,
            ci.category as category
        ORDER BY r.name, c.number, s.number
        """
        
        return self.conn.query(query, {'deadline_type': deadline_type})
    
    # ========================================================================
    # QUERY 6: Graph Traversal - Related Sections
    # ========================================================================
    
    def find_related_sections(self, section_number: str, regulation: str, depth: int = 2) -> List[Dict]:
        """
        Find sections related through graph structure
        
        Useful for understanding context and dependencies
        """
        query = """
        MATCH (r:Regulation {id: $regulation})-[:HAS_CHAPTER]->(c:Chapter)-[:HAS_SECTION]->(s:Section {number: $section_number})
        MATCH (c)-[:HAS_SECTION]->(related:Section)
        WHERE related.number <> s.number
        RETURN 
            related.number as section_number,
            related.title as section_title,
            related.summary as summary
        LIMIT 10
        """
        
        return self.conn.query(query, {
            'section_number': section_number,
            'regulation': regulation
        })
    
    # ========================================================================
    # QUERY 7: Multi-hop Reasoning
    # ========================================================================
    
    def find_requirements_by_entity_type(self, entity_type: str) -> List[Dict]:
        """
        Find requirements that apply to specific entity types
        
        entity_type: 'public_issue', 'rights_issue', 'preferential_issue', etc.
        """
        query = """
        MATCH (r:Regulation)-[:HAS_CHAPTER]->(c:Chapter)-[:HAS_SECTION]->(s:Section)-[:REQUIRES]->(ci:ComplianceItem)
        WHERE $entity_type IN ci.applies_to OR 'all_issues' IN ci.applies_to
        RETURN 
            r.name as regulation,
            c.title as chapter,
            s.number as section_number,
            s.title as section_title,
            ci.requirement_text as requirement,
            ci.mandatory as mandatory,
            ci.category as category,
            ci.applies_to as applies_to
        ORDER BY r.name, ci.mandatory DESC, c.number
        """
        
        return self.conn.query(query, {'entity_type': entity_type})
    
    # ========================================================================
    # QUERY 8: Compliance Checklist Generator
    # ========================================================================
    
    def generate_compliance_checklist(self, regulation: str, chapter: Optional[str] = None) -> Dict:
        """
        Generate a compliance checklist for a regulation or chapter
        
        Returns organized by category and timeline
        """
        query = """
        MATCH (r:Regulation {id: $regulation})-[:HAS_CHAPTER]->(c:Chapter)-[:HAS_SECTION]->(s:Section)-[:REQUIRES]->(ci:ComplianceItem)
        WHERE $chapter IS NULL OR c.number = $chapter
        WITH ci.category as category,
             ci.deadline_type as deadline,
             collect({
                 requirement: ci.requirement_text,
                 mandatory: ci.mandatory,
                 section: s.number,
                 chapter: c.number
             }) as items
        RETURN category, deadline, items
        ORDER BY category, deadline
        """
        
        results = self.conn.query(query, {
            'regulation': regulation,
            'chapter': chapter
        })
        
        # Organize into structured checklist
        checklist = {
            'pre_filing': {},
            'at_filing': {},
            'post_approval': {},
            'ongoing': {}
        }
        
        for result in results:
            deadline = result['deadline']
            category = result['category']
            
            if deadline not in checklist:
                checklist[deadline] = {}
            
            if category not in checklist[deadline]:
                checklist[deadline][category] = []
            
            checklist[deadline][category].extend(result['items'])
        
        return checklist
    
    # ========================================================================
    # QUERY 9: Similarity Search (for RAG)
    # ========================================================================
    
    def semantic_search(self, query_text: str, top_k: int = 5) -> List[Dict]:
        """
        Perform semantic search across all sections
        
        This would typically use vector embeddings, but we're using full-text here
        """
        cypher_query = """
        CALL db.index.fulltext.queryNodes('section_text', $query)
        YIELD node as s, score
        MATCH (s:Section)<-[:HAS_SECTION]-(c:Chapter)<-[:HAS_CHAPTER]-(r:Regulation)
        OPTIONAL MATCH (s)-[:REQUIRES]->(ci:ComplianceItem)
        RETURN 
            r.name as regulation,
            c.number as chapter_number,
            c.title as chapter_title,
            s.number as section_number,
            s.title as section_title,
            s.summary as summary,
            collect(DISTINCT ci.requirement_text) as requirements,
            score
        ORDER BY score DESC
        LIMIT $top_k
        """
        
        return self.conn.query(cypher_query, {
            'query': query_text,
            'top_k': top_k
        })
    
    # ========================================================================
    # QUERY 10: Get Graph Statistics
    # ========================================================================
    
    def get_statistics(self) -> Dict:
        """
        Get statistics about the knowledge graph
        """
        stats_query = """
        MATCH (r:Regulation)
        OPTIONAL MATCH (r)-[:HAS_CHAPTER]->(c:Chapter)
        OPTIONAL MATCH (c)-[:HAS_SECTION]->(s:Section)
        OPTIONAL MATCH (s)-[:REQUIRES]->(ci:ComplianceItem)
        RETURN 
            count(DISTINCT r) as regulations,
            count(DISTINCT c) as chapters,
            count(DISTINCT s) as sections,
            count(DISTINCT ci) as compliance_items
        """
        
        result = self.conn.query(stats_query)[0]
        
        # Category breakdown
        category_query = """
        MATCH (ci:ComplianceItem)
        RETURN ci.category as category, count(*) as count
        ORDER BY count DESC
        """
        
        categories = self.conn.query(category_query)
        
        return {
            'total_regulations': result['regulations'],
            'total_chapters': result['chapters'],
            'total_sections': result['sections'],
            'total_compliance_items': result['compliance_items'],
            'by_category': {cat['category']: cat['count'] for cat in categories}
        }

# ============================================================================
# EXAMPLE USAGE
# ============================================================================

def demo_queries():
    """
    Demonstrate various query patterns
    """
    rag = LegalGraphRAG()
    
    print("=" * 80)
    print("GRAPH RAG QUERY DEMONSTRATIONS")
    print("=" * 80)
    
    # Query 1: Topic search
    print("\n1. Requirements for 'prospectus':")
    results = rag.find_requirements_by_topic("prospectus")
    for r in results[:3]:
        print(f"   - {r.section}: {r.requirement[:100]}...")
    
    # Query 2: By category
    print("\n2. All Disclosure requirements:")
    disc_reqs = rag.find_by_category("Disclosure", mandatory_only=True)
    print(f"   Found {len(disc_reqs)} mandatory disclosure requirements")
    
    # Query 3: Timeline
    print("\n3. Pre-filing requirements:")
    pre_filing = rag.get_timeline_requirements("pre-filing")
    print(f"   Found {len(pre_filing)} pre-filing requirements")
    
    # Query 4: Checklist
    print("\n4. Generating compliance checklist...")
    checklist = rag.generate_compliance_checklist("COMPANIES_ACT", chapter="III")
    print(f"   Generated checklist with {len(checklist)} timeline categories")
    
    # Query 5: Statistics
    print("\n5. Knowledge Graph Statistics:")
    stats = rag.get_statistics()
    print(f"   Regulations: {stats['total_regulations']}")
    print(f"   Chapters: {stats['total_chapters']}")
    print(f"   Sections: {stats['total_sections']}")
    print(f"   Compliance Items: {stats['total_compliance_items']}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    demo_queries()