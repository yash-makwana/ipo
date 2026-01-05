from semantic_legal_search import get_semantic_search

# Test obligation retrieval
search = get_semantic_search('ICDR')

# Test 1: Search with chapter filter
results = search.vector_search(
    query="employee disclosure requirements",
    chapter_filter=["Schedule VIII"],
    section_filter=["Part A"],
    top_k=5
)

for r in results:
    print(f"✅ {r['citation']}")
    print(f"   {r['requirement_text'][:100]}...")
    print(f"   Score: {r['similarity_score']:.3f}")
    print()

# Test 2: Get all obligations for a chapter
all_obligations = search.get_obligations_by_chapter(
    chapter="Schedule VIII",
    section="Part A",
    mandatory_only=True
)

print(f"Found {len(all_obligations)} mandatory obligations in Schedule VIII Part A")