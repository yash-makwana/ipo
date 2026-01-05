import os
import sys

# Ensure project root is importable when running tests directly
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from content_extraction_engine import ContentExtractionEngine


def test_extract_complete_context_simple_products_and_page_map():
    engine = ContentExtractionEngine()

    # Construct a minimal pages_dict with a table-like line and narrative triggers
    pages_dict = {
        1: "ProductA ₹100 ₹200 ₹300\nProductB ₹50 ₹60 ₹70\n",
        2: "Our products include: Widget X, Widget Y and Widget Z.\nMore narrative here.",
        3: "This is a revenue table: product wise revenue and other notes.",
        4: "Risk Factors: competition and market position are discussed."
    }

    context = engine.extract_complete_context(pages_dict)

    # Assertions: products detected, page_map contains business_overview or revenue_tables
    assert 'products' in context
    assert len(context['products']) >= 1
    assert 'page_map' in context
    # Either revenue_tables or business_overview should be mapped
    assert any(topic in context['page_map'] for topic in ['revenue_tables', 'business_overview'])
