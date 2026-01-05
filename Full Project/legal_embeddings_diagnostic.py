"""
Legal Embeddings Diagnostic Tool
=================================
Comprehensive verification and quality checks for legal document embeddings

Features:
- Neo4j connectivity test
- Data integrity checks
- Embedding quality analysis
- Search accuracy validation
- Performance benchmarks
"""

from neo4j import GraphDatabase
from google.cloud import aiplatform
from vertexai.language_models import TextEmbeddingModel
import os
import sys
import time
import numpy as np
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# Configuration
# ============================================================================

NEO4J_URI = os.environ.get('NEO4J_URI')
NEO4J_USER = os.environ.get('NEO4J_USER')
NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD')
PROJECT_ID = os.environ.get('GCP_PROJECT')

# ============================================================================
# Diagnostic Class
# ============================================================================

class LegalEmbeddingsDiagnostic:
    """Comprehensive diagnostic tool"""
    
    def __init__(self):
        print("🔧 Initializing diagnostic tool...")
        
        # Neo4j connection
        try:
            self.driver = GraphDatabase.driver(
                NEO4J_URI,
                auth=(NEO4J_USER, NEO4J_PASSWORD)
            )
            print("✅ Neo4j connected")
        except Exception as e:
            print(f"❌ Neo4j connection failed: {e}")
            sys.exit(1)
        
        # Vertex AI
        try:
            aiplatform.init(project=PROJECT_ID, location="us-central1")
            self.embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")
            print("✅ Vertex AI initialized")
        except Exception as e:
            print(f"⚠️  Vertex AI initialization failed: {e}")
            self.embedding_model = None
    
    def close(self):
        """Close connections"""
        self.driver.close()
    
    # ========================================================================
    # Test 1: Neo4j Connection and Schema
    # ========================================================================
    
    def test_neo4j_connection(self) -> bool:
        """Test Neo4j connectivity"""
        print("\n" + "=" * 80)
        print("TEST 1: Neo4j Connection")
        print("=" * 80)
        
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                value = result.single()['test']
                assert value == 1
            
            print("✅ Connection successful")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def test_schema_indexes(self) -> Dict:
        """Check if all indexes exist"""
        print("\n" + "=" * 80)
        print("TEST 2: Schema and Indexes")
        print("=" * 80)
        
        with self.driver.session() as session:
            # Check indexes
            result = session.run("SHOW INDEXES")
            indexes = [record['name'] for record in result]
            
            expected_indexes = [
                'regulation_id',
                'chapter_id',
                'chunk_id'
            ]
            
            print("\nIndexes found:")
            for idx in indexes:
                print(f"  • {idx}")
            
            # Check for vector index
            has_vector_index = any('vector' in idx.lower() or 'embedding' in idx.lower() for idx in indexes)
            
            if has_vector_index:
                print("✅ Vector index found")
            else:
                print("⚠️  Vector index not found (may impact performance)")
            
            # Check constraints
            result = session.run("SHOW CONSTRAINTS")
            constraints = [record['name'] for record in result]
            
            print("\nConstraints found:")
            if constraints:
                for constraint in constraints:
                    print(f"  • {constraint}")
            else:
                print("  (none)")
            
            return {
                'indexes': indexes,
                'has_vector_index': has_vector_index,
                'constraints': constraints
            }
    
    # ========================================================================
    # Test 3: Data Integrity
    # ========================================================================
    
    def test_data_integrity(self) -> Dict:
        """Verify data completeness and integrity"""
        print("\n" + "=" * 80)
        print("TEST 3: Data Integrity")
        print("=" * 80)
        
        stats = {}
        
        with self.driver.session() as session:
            # Count regulations
            result = session.run("MATCH (r:Regulation) RETURN count(*) as count")
            stats['regulations'] = result.single()['count']
            print(f"\n📊 Regulations: {stats['regulations']}")
            
            # Count chapters
            result = session.run("MATCH (c:Chapter) RETURN count(*) as count")
            stats['chapters'] = result.single()['count']
            print(f"📊 Chapters: {stats['chapters']}")
            
            # Count chunks
            result = session.run("MATCH (ch:LegalChunk) RETURN count(*) as count")
            stats['chunks'] = result.single()['count']
            print(f"📊 Legal Chunks: {stats['chunks']}")
            
            # Count chunks with embeddings
            result = session.run("""
                MATCH (ch:LegalChunk)
                WHERE ch.embedding IS NOT NULL
                RETURN count(*) as count
            """)
            stats['chunks_with_embeddings'] = result.single()['count']
            print(f"📊 Chunks with Embeddings: {stats['chunks_with_embeddings']}")
            
            # Check embedding dimensions
            result = session.run("""
                MATCH (ch:LegalChunk)
                WHERE ch.embedding IS NOT NULL
                RETURN size(ch.embedding) as dim
                LIMIT 1
            """)
            record = result.single()
            if record:
                stats['embedding_dimension'] = record['dim']
                print(f"📊 Embedding Dimension: {stats['embedding_dimension']}")
            
            # Check for orphaned nodes
            result = session.run("""
                MATCH (ch:LegalChunk)
                WHERE NOT (ch)<-[:CONTAINS]-()
                RETURN count(*) as count
            """)
            orphaned = result.single()['count']
            stats['orphaned_chunks'] = orphaned
            
            if orphaned > 0:
                print(f"⚠️  Orphaned chunks: {orphaned}")
            else:
                print("✅ No orphaned chunks")
            
            # Check regulation details
            result = session.run("""
                MATCH (r:Regulation)
                RETURN r.short_name as name, r.type as type
            """)
            
            print("\n📋 Regulations:")
            for record in result:
                print(f"  • {record['name']} ({record['type']})")
            
            # Validation
            if stats['chunks'] == stats['chunks_with_embeddings']:
                print("\n✅ All chunks have embeddings")
            else:
                missing = stats['chunks'] - stats['chunks_with_embeddings']
                print(f"\n⚠️  {missing} chunks missing embeddings")
            
            if stats['embedding_dimension'] == 768:
                print("✅ Embedding dimension correct (768)")
            else:
                print(f"❌ Incorrect embedding dimension: {stats['embedding_dimension']}")
        
        return stats
    
    # ========================================================================
    # Test 4: Embedding Quality
    # ========================================================================
    
    def test_embedding_quality(self) -> Dict:
        """Analyze embedding quality"""
        print("\n" + "=" * 80)
        print("TEST 4: Embedding Quality Analysis")
        print("=" * 80)
        
        with self.driver.session() as session:
            # Get sample embeddings
            result = session.run("""
                MATCH (ch:LegalChunk)
                WHERE ch.embedding IS NOT NULL
                RETURN ch.chunk_id as id, ch.embedding as embedding, ch.text as text
                LIMIT 100
            """)
            
            embeddings = []
            texts = []
            
            for record in result:
                embeddings.append(np.array(record['embedding']))
                texts.append(record['text'][:100])
            
            if len(embeddings) == 0:
                print("❌ No embeddings found")
                return {}
            
            embeddings_array = np.array(embeddings)
            
            # Calculate statistics
            norms = np.linalg.norm(embeddings_array, axis=1)
            
            stats = {
                'sample_size': len(embeddings),
                'avg_norm': float(np.mean(norms)),
                'std_norm': float(np.std(norms)),
                'min_norm': float(np.min(norms)),
                'max_norm': float(np.max(norms))
            }
            
            print(f"\n📊 Sample Size: {stats['sample_size']}")
            print(f"📊 Average Norm: {stats['avg_norm']:.4f}")
            print(f"📊 Std Dev: {stats['std_norm']:.4f}")
            print(f"📊 Min Norm: {stats['min_norm']:.4f}")
            print(f"📊 Max Norm: {stats['max_norm']:.4f}")
            
            # Check for zero vectors
            zero_vectors = np.sum(np.all(embeddings_array == 0, axis=1))
            stats['zero_vectors'] = int(zero_vectors)
            
            if zero_vectors > 0:
                print(f"⚠️  Zero vectors found: {zero_vectors}")
            else:
                print("✅ No zero vectors")
            
            # Calculate pairwise similarities (sample)
            if len(embeddings) >= 10:
                sample_embeddings = embeddings_array[:10]
                similarities = np.dot(sample_embeddings, sample_embeddings.T)
                
                # Normalize
                norms_sample = np.linalg.norm(sample_embeddings, axis=1)
                similarities = similarities / np.outer(norms_sample, norms_sample)
                
                # Get off-diagonal elements
                mask = ~np.eye(10, dtype=bool)
                off_diagonal = similarities[mask]
                
                stats['avg_similarity'] = float(np.mean(off_diagonal))
                stats['max_similarity'] = float(np.max(off_diagonal))
                
                print(f"\n📊 Avg Pairwise Similarity: {stats['avg_similarity']:.4f}")
                print(f"📊 Max Pairwise Similarity: {stats['max_similarity']:.4f}")
                
                if stats['avg_similarity'] > 0.9:
                    print("⚠️  Embeddings may be too similar (possible issue)")
                elif stats['avg_similarity'] < 0.1:
                    print("⚠️  Embeddings may be too dissimilar (possible issue)")
                else:
                    print("✅ Embedding similarity looks good")
        
        return stats
    
    # ========================================================================
    # Test 5: Search Accuracy
    # ========================================================================
    
    def test_search_accuracy(self) -> Dict:
        """Test semantic search accuracy"""
        print("\n" + "=" * 80)
        print("TEST 5: Search Accuracy")
        print("=" * 80)
        
        if not self.embedding_model:
            print("⚠️  Skipping (Vertex AI not available)")
            return {}
        
        # Test queries with expected results
        test_cases = [
            {
                'query': 'risk factors disclosure requirements',
                'expected_regulation': 'ICDR',
                'expected_keywords': ['risk', 'factor', 'disclosure']
            },
            {
                'query': 'directors appointment and qualification',
                'expected_regulation': 'COMPANIES_ACT',
                'expected_keywords': ['director', 'appointment']
            },
            {
                'query': 'objects of the issue',
                'expected_regulation': 'ICDR',
                'expected_keywords': ['object', 'issue']
            }
        ]
        
        results = []
        
        for i, test in enumerate(test_cases, 1):
            print(f"\n🔍 Test Case {i}: '{test['query']}'")
            
            # Generate query embedding
            query_embedding = self.embedding_model.get_embeddings([test['query']])[0].values
            
            # Search Neo4j
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (r:Regulation)-[:HAS_CHAPTER]->(c:Chapter)-[:CONTAINS]->(ch:LegalChunk)
                    WITH ch, r,
                         gds.similarity.cosine(ch.embedding, $query_embedding) as similarity
                    WHERE similarity > 0.3
                    RETURN 
                        ch.chunk_id as chunk_id,
                        ch.text as text,
                        r.short_name as regulation,
                        similarity
                    ORDER BY similarity DESC
                    LIMIT 5
                """, {'query_embedding': query_embedding})
                
                matches = []
                for record in result:
                    matches.append({
                        'chunk_id': record['chunk_id'],
                        'regulation': record['regulation'],
                        'text': record['text'][:200],
                        'similarity': float(record['similarity'])
                    })
                
                if matches:
                    top_match = matches[0]
                    print(f"  Top match: {top_match['regulation']} (score: {top_match['similarity']:.3f})")
                    print(f"  Text: {top_match['text'][:100]}...")
                    
                    # Check if correct regulation
                    correct_reg = top_match['regulation'] == test['expected_regulation']
                    
                    # Check for keywords
                    text_lower = top_match['text'].lower()
                    keywords_found = sum(1 for kw in test['expected_keywords'] if kw.lower() in text_lower)
                    
                    test_result = {
                        'query': test['query'],
                        'expected_regulation': test['expected_regulation'],
                        'actual_regulation': top_match['regulation'],
                        'correct_regulation': correct_reg,
                        'similarity_score': top_match['similarity'],
                        'keywords_found': keywords_found,
                        'total_keywords': len(test['expected_keywords'])
                    }
                    
                    results.append(test_result)
                    
                    if correct_reg and keywords_found >= len(test['expected_keywords']) / 2:
                        print("  ✅ Test passed")
                    else:
                        print("  ⚠️  Test partially passed")
                else:
                    print("  ❌ No matches found")
                    results.append({
                        'query': test['query'],
                        'correct_regulation': False,
                        'similarity_score': 0
                    })
        
        # Calculate accuracy
        total_tests = len(results)
        correct_tests = sum(1 for r in results if r.get('correct_regulation', False))
        accuracy = (correct_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n📊 Search Accuracy: {accuracy:.1f}% ({correct_tests}/{total_tests})")
        
        if accuracy >= 80:
            print("✅ Search accuracy is good")
        elif accuracy >= 60:
            print("⚠️  Search accuracy is acceptable")
        else:
            print("❌ Search accuracy needs improvement")
        
        return {
            'accuracy': accuracy,
            'test_results': results
        }
    
    # ========================================================================
    # Test 6: Performance Benchmark
    # ========================================================================
    
    def test_performance(self) -> Dict:
        """Benchmark search performance"""
        print("\n" + "=" * 80)
        print("TEST 6: Performance Benchmark")
        print("=" * 80)
        
        if not self.embedding_model:
            print("⚠️  Skipping (Vertex AI not available)")
            return {}
        
        # Generate test query
        test_query = "disclosure requirements for financial statements"
        query_embedding = self.embedding_model.get_embeddings([test_query])[0].values
        
        # Benchmark vector search
        print("\n🏃 Running 10 vector searches...")
        
        times = []
        
        for i in range(10):
            start = time.time()
            
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (ch:LegalChunk)
                    WHERE ch.embedding IS NOT NULL
                    WITH ch, gds.similarity.cosine(ch.embedding, $query_embedding) as similarity
                    WHERE similarity > 0.3
                    RETURN ch.chunk_id, similarity
                    ORDER BY similarity DESC
                    LIMIT 10
                """, {'query_embedding': query_embedding})
                
                _ = list(result)
            
            elapsed = (time.time() - start) * 1000  # ms
            times.append(elapsed)
        
        avg_time = np.mean(times)
        min_time = np.min(times)
        max_time = np.max(times)
        p95_time = np.percentile(times, 95)
        
        print(f"\n📊 Average: {avg_time:.1f}ms")
        print(f"📊 Min: {min_time:.1f}ms")
        print(f"📊 Max: {max_time:.1f}ms")
        print(f"📊 P95: {p95_time:.1f}ms")
        
        if avg_time < 200:
            print("✅ Performance is excellent")
        elif avg_time < 500:
            print("✅ Performance is good")
        elif avg_time < 1000:
            print("⚠️  Performance is acceptable")
        else:
            print("❌ Performance needs improvement (consider adding vector index)")
        
        return {
            'avg_time_ms': float(avg_time),
            'min_time_ms': float(min_time),
            'max_time_ms': float(max_time),
            'p95_time_ms': float(p95_time)
        }
    
    # ========================================================================
    # Run All Tests
    # ========================================================================
    
    def run_all_tests(self):
        """Run comprehensive diagnostic"""
        print("\n" + "=" * 80)
        print("🔬 LEGAL EMBEDDINGS COMPREHENSIVE DIAGNOSTIC")
        print("=" * 80)
        
        all_results = {}
        
        # Test 1: Connection
        all_results['connection'] = self.test_neo4j_connection()
        
        if not all_results['connection']:
            print("\n❌ Cannot proceed without Neo4j connection")
            return
        
        # Test 2: Schema
        all_results['schema'] = self.test_schema_indexes()
        
        # Test 3: Data Integrity
        all_results['integrity'] = self.test_data_integrity()
        
        # Test 4: Embedding Quality
        all_results['quality'] = self.test_embedding_quality()
        
        # Test 5: Search Accuracy
        all_results['accuracy'] = self.test_search_accuracy()
        
        # Test 6: Performance
        all_results['performance'] = self.test_performance()
        
        # Final Summary
        print("\n" + "=" * 80)
        print("📊 DIAGNOSTIC SUMMARY")
        print("=" * 80)
        
        print(f"\n✅ Neo4j Connection: OK")
        print(f"✅ Data Integrity: {all_results['integrity'].get('chunks', 0)} chunks loaded")
        print(f"✅ Embeddings: {all_results['integrity'].get('chunks_with_embeddings', 0)} / {all_results['integrity'].get('chunks', 0)}")
        
        if all_results.get('accuracy'):
            print(f"✅ Search Accuracy: {all_results['accuracy'].get('accuracy', 0):.1f}%")
        
        if all_results.get('performance'):
            print(f"✅ Performance: {all_results['performance'].get('avg_time_ms', 0):.1f}ms avg")
        
        print("\n" + "=" * 80)
        
        return all_results


# ============================================================================
# Main Execution
# ============================================================================

def main():
    """Run diagnostic"""
    diagnostic = LegalEmbeddingsDiagnostic()
    
    try:
        results = diagnostic.run_all_tests()
        
        # Save results
        import json
        with open('diagnostic_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print("\n💾 Results saved to: diagnostic_results.json")
        
    finally:
        diagnostic.close()


if __name__ == "__main__":
    main()
