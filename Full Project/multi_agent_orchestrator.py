"""
Multi-Agent Compliance Orchestrator - NSE-GRADE WITH 4 ADVANCED DIMENSIONS
===========================================================================
Complete NSE-aligned orchestrator with:
✅ System A: Internal compliance validation (silent)
✅ System B: NSE content review (user-visible)
✅ System C: IPO applicability filtering (prevents spam)
✅ Interpretation & Normalization Layer (context intelligence)
✅ NEW: 4 Advanced Intelligence Dimensions (forensic-grade)

Architecture:
    DRHP PDF
       ↓
    Document Processing + Page Extraction
       ↓
    IPO Structure Detection
       ↓
    ┌──────────────┴──────────────┐
    │                             │
System A                      System B
(Internal Compliance)         (NSE Content Review)
    │                             │
    ↓                             ↓
 Neo4j Findings            Checklist Findings
    │                             │
    └──────────────┬──────────────┘
                   ↓
    🧠 INTERPRETATION & NORMALIZATION 🧠
    (Business Model, Materiality, Severity, Merging)
                   ↓
    🔬 4 ADVANCED INTELLIGENCE DIMENSIONS 🔬
    1. Contradiction Detection (numeric/entity/category)
    2. Entity Identity Tracking (semantic consistency)
    3. Purpose Interrogation (why/impact/dependency)
    4. Drafting Hygiene (footnotes/acronyms/formatting)
                   ↓
         NSE-Grade Calibrated Queries
         (95%+ Accuracy Target)
"""

import time
from typing import List, Dict, Any, Optional
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.retrieval_agent import RetrievalAgent
from agents.analysis_agent import AnalysisAgent
from agents.validation_agent import ValidationAgent
from agents.reanalysis_agent import ReanalysisAgent
from agents.synthesis_agent import SynthesisAgent

from nse_engine_adapter import get_nse_engine_adapter
from ipo_applicability_engine import IPOApplicabilityEngine
from nse_output_formatter import format_nse_output, format_nse_section
from interpretation_normalization_layer import get_interpretation_layer
from advanced_intelligence_layers import get_advanced_intelligence_layers
from content_extraction_engine import get_content_extraction_engine  # ✅ NEW
from context_aware_query_generators import get_context_aware_generator  # ✅ NEW
from state_models import create_initial_state
from semantic_legal_search import get_semantic_search
from document_processor_local import DocumentProcessor


class MultiAgentComplianceOrchestrator:
    """
    NSE-ALIGNED ORCHESTRATOR (PRODUCTION GRADE)
    
    Features:
    - IPO structure detection and applicability filtering
    - System A runs silently (internal validation)
    - System B generates NSE-style queries (user-visible)
    - No regulatory spam (only applicable obligations checked)
    """
    
    def __init__(self, regulation_type: str = "ICDR"):
        """Initialize NSE-aligned orchestrator with all systems"""
        self.regulation_type = regulation_type
        
        # System A: Internal Compliance Agents
        self.retrieval_agent = RetrievalAgent(regulation_type)
        self.analysis_agent = AnalysisAgent(regulation_type)
        self.validation_agent = ValidationAgent()
        self.reanalysis_agent = ReanalysisAgent(regulation_type)
        self.synthesis_agent = SynthesisAgent()
        
        # System B: NSE Content Review (Enhanced with SystemB Engines)
        self.content_review_agent = get_nse_engine_adapter()
        
        # System C: IPO Applicability Engine
        self.applicability_engine = IPOApplicabilityEngine()
        
        # 🧠 Interpretation & Normalization Layer
        self.normalization_layer = get_interpretation_layer()
        
        # 🔬 Advanced Intelligence Layers (4 Dimensions)
        self.advanced_layers = get_advanced_intelligence_layers()
        
        # 🎯 Content Extraction Engine (NEW - Makes system work on ANY DRHP)
        self.content_extractor = get_content_extraction_engine()
        
        # 🔍 Context-Aware Query Generators (NEW - DRHP-specific queries)
        self.context_aware_generator = get_context_aware_generator()
        
        # Database
        try:
            self.semantic_search = get_semantic_search(regulation_type)
            print(f"✅ NSE-Grade Multi-Agent Orchestrator Initialized")
            print(f"   ✓ System A: Internal Compliance")
            print(f"   ✓ System B: NSE Content Review (Enhanced)")
            print(f"   ✓ System C: Applicability Filtering")
            print(f"   ✓ 🧠 Normalization Layer (Context Intelligence)")
            print(f"   ✓ 🔬 Advanced Intelligence (4 Dimensions)")
            print(f"   ✓ 🎯 Content Extraction (DRHP-Specific)")
            print(f"   ✓ 🔍 Context-Aware Generators (Generic→Specific)")
        except Exception as e:
            print(f"⚠️  Semantic search unavailable: {e}")
            self.semantic_search = None
    
    # ========================================================================
    # PUBLIC ENTRYPOINT
    # ========================================================================
    
    def check_drhp_compliance(
        self,
        drhp_file_path: str,
        drhp_chapter: str,
        chapter_filters: List[str] = None,
        mandatory_only: bool = False,
        initial_limit: int = 30,
        run_internal_checks: bool = True,
        output_format: str = "structured"  # "structured" or "nse_text"
    ) -> Dict[str, Any]:
        """
        Complete DRHP compliance check with NSE-aligned output
        
        Args:
            drhp_file_path: Path to DRHP PDF
            drhp_chapter: Chapter name (e.g., "Business Overview")
            chapter_filters: Neo4j chapters to check (System A)
            mandatory_only: Only check mandatory obligations (System A)
            initial_limit: Max obligations per chapter (System A)
            run_internal_checks: Whether to run System A (default: True)
            output_format: "structured" (dict) or "nse_text" (formatted string)
        
        Returns:
            NSE-style compliance results
        """
        
        print(f"\n{'='*80}")
        print(f"🚀 NSE-ALIGNED COMPLIANCE CHECK")
        print(f"{'='*80}")
        print(f"   DRHP Chapter: {drhp_chapter}")
        print(f"   Output Format: {output_format}")
        print(f"{'='*80}\n")
        
        start_time = time.time()
        
        # ====================================================================
        # STEP 1: PROCESS DRHP DOCUMENT
        # ====================================================================
        
        print(f"📄 Step 1: Processing DRHP...")
        doc_processor = DocumentProcessor()
        document_chunks = doc_processor.process_pdf_with_pages(drhp_file_path)
        print(f"   ✅ Processed {len(document_chunks)} chunks")
        
        # Extract metadata
        company_name = self._extract_company_name(document_chunks)
        company_profile = self._extract_company_profile(document_chunks)
        
        print(f"   🏢 Company: {company_name}")
        print(f"   📊 Profile: Revenue=₹{company_profile['revenue']} Cr, "
              f"Employees={company_profile['employees']}, Type={company_profile['business_type']}")
        
        # ====================================================================
        # STEP 2: DETECT IPO STRUCTURE (APPLICABILITY)
        # ====================================================================
        
        print(f"\n🔍 Step 2: Detecting IPO Structure...")
        full_text = "\n".join([c.get('text', '') for c in document_chunks[:100]])  # First 100 chunks
        ipo_profile = self.applicability_engine.infer(full_text)
        
        print(f"   IPO Structure Detected:")
        print(f"   - Convertible Debt: {ipo_profile['has_convertible_debt']}")
        print(f"   - Warrants: {ipo_profile['has_warrants']}")
        print(f"   - Secured Instruments: {ipo_profile['has_secured_instruments']}")
        print(f"   - SR Shares: {ipo_profile['has_sr_shares']}")
        print(f"   - VC/PE Investors: {ipo_profile['has_vc_or_pe']}")
        print(f"   - Employee Equity: {ipo_profile['has_employee_equity']}")
        
        # ====================================================================
        # STEP 2.5: 🎯 EXTRACT DRHP-SPECIFIC CONTENT (NEW - THE KEY!)
        # ====================================================================
        
        print(f"\n🎯 Step 2.5: Extracting DRHP-Specific Context...")
        
        # Prepare pages dictionary
        pages_dict = self._prepare_pages_dict(document_chunks)
        
        # Extract complete context
        drhp_context = self.content_extractor.extract_complete_context(pages_dict)
        
        print(f"   ✅ Context extracted:")
        print(f"      Products: {drhp_context['metadata']['products_count']}")
        print(f"      Segments: {drhp_context['metadata']['segments_count']}")
        print(f"      Anomalies: {drhp_context['metadata']['anomalies_count']}")
        print(f"      Entities: {drhp_context['metadata']['entities_count']}")
        
        # ====================================================================
        # EXPECTATION LOCKING: Ensure intent-locked questions are produced
        # ====================================================================
        try:
            from expectation_locker import get_expectation_locker
            locker = get_expectation_locker()
            expectation_questions = locker.detect_and_lock(drhp_context, pages_dict)
            # Store a local mapped form that we can merge into nse_queries prior to normalization
            expectation_queries_local = []
            if expectation_questions:
                print(f"\n🔐 ExpectationLocker emitted {len(expectation_questions)} locked question(s)")
                for q in expectation_questions:
                    expectation_queries_local.append({
                        'type': 'nse_expectation_question',
                        'page': 'N/A',
                        'observation': q['question'],
                        'severity': 'Material',
                        'category': 'Expectation',
                        'locked': True,
                        'issue_id': q['expectation_id']
                    })
        except Exception as e:
            print(f"⚠️  ExpectationLocker error: {e}")

        # ====================================================================
        # STEP 3: SYSTEM A - INTERNAL COMPLIANCE (SILENT)
        # ====================================================================
        
        if run_internal_checks and self.semantic_search and chapter_filters:
            print(f"\n⚖️  Step 3: Running Internal Compliance Checks...")
            internal_stats = self._run_internal_compliance_checks(
                document_chunks=document_chunks,
                drhp_chapter=drhp_chapter,
                chapter_filters=chapter_filters,
                mandatory_only=mandatory_only,
                initial_limit=initial_limit,
                ipo_profile=ipo_profile  # ✅ PASS IPO PROFILE FOR FILTERING
            )
            print(f"   ✅ Checked {internal_stats['total_checked']} applicable obligations")
            print(f"   ⏭️  Skipped {internal_stats['total_skipped']} non-applicable obligations")
        else:
            print(f"\n⏭️  Step 3: Skipping Internal Compliance Checks")
            internal_stats = {'total_checked': 0, 'total_skipped': 0}
        
        # ====================================================================
        # STEP 4: SYSTEM B - NSE CONTENT REVIEW (USER-VISIBLE)
        # ====================================================================
        
        print(f"\n📋 Step 4: Generating NSE Content Queries...")
        nse_queries = self._run_nse_content_review(
            document_chunks=document_chunks,
            company_name=company_name,
            company_profile=company_profile,
            ipo_profile=ipo_profile,  # ✅ PASS FOR ADDITIONAL FILTERING
            drhp_file_path=drhp_file_path  # ✅ PASS PDF PATH FOR PAGE EXTRACTION
        )
        
        print(f"   ✅ Generated {len(nse_queries)} raw NSE-style queries")
        
        # ====================================================================
        # STEP 5: 🧠 INTERPRETATION & NORMALIZATION (NEW - THE MISSING LAYER)
        # ====================================================================
        
        # Pass through normalization layer for context intelligence
        print(f"\n🧠 Step 5: Running Interpretation & Normalization...")
        # Merge expectation queries (if any) into NSE queries so they go through normalization
        if 'expectation_queries_local' in locals() and expectation_queries_local:
            print(f"   🔁 Merging {len(expectation_queries_local)} expectation question(s) into NSE queries for normalization")
            nse_queries.extend(expectation_queries_local)

        nse_queries = self.normalization_layer.normalize(
            queries=nse_queries,
            company_profile=company_profile,
            drhp_text=None  # Can pass full text if needed
        )
        
        print(f"   ✅ Normalized to {len(nse_queries)} calibrated queries")
        if nse_queries:
            severity_counts = {}
            for q in nse_queries:
                sev = q.get('severity', 'Unknown')
                severity_counts[sev] = severity_counts.get(sev, 0) + 1
            
            for sev, count in severity_counts.items():
                print(f"      - {sev}: {count}")
        
        # ====================================================================
        # STEP 6: 🔬 ADVANCED INTELLIGENCE LAYERS (4 DIMENSIONS) - NEW
        # ====================================================================
        
        print(f"\n🔬 Step 6: Running Advanced Intelligence Layers...")
        
        # Prepare pages dictionary for advanced analysis
        pages_dict = self._prepare_pages_dict(document_chunks)
        
        # Run all 4 dimensions
        advanced_results = self.advanced_layers.run_all_dimensions(pages_dict)
        
        # Combine all advanced queries
        advanced_queries = []
        advanced_queries.extend(advanced_results.get('contradictions', []))
        advanced_queries.extend(advanced_results.get('entity_identity', []))
        advanced_queries.extend(advanced_results.get('purpose_interrogation', []))
        advanced_queries.extend(advanced_results.get('hygiene', []))
        
        print(f"   ✅ Advanced layers generated {len(advanced_queries)} additional queries")
        print(f"      - Contradictions: {len(advanced_results.get('contradictions', []))}")
        print(f"      - Entity Identity: {len(advanced_results.get('entity_identity', []))}")
        print(f"      - Purpose Interrogation: {len(advanced_results.get('purpose_interrogation', []))}")
        print(f"      - Hygiene: {len(advanced_results.get('hygiene', []))}")
        
        # ====================================================================
        # STEP 6.5: 🔍 CONTEXT-AWARE QUERY GENERATION (NEW - THE GAME CHANGER!)
        # ====================================================================
        
        print(f"\n🔍 Step 6.5: Generating Context-Aware Queries...")
        
        # Generate DRHP-specific queries using extracted context
        context_aware_results = self.context_aware_generator.generate_all_queries(
            context=drhp_context,
            pages_dict=pages_dict
        )
        
        # Combine all context-aware queries
        context_aware_queries = []
        context_aware_queries.extend(context_aware_results.get('financial', []))
        context_aware_queries.extend(context_aware_results.get('operational', []))
        context_aware_queries.extend(context_aware_results.get('cross_reference', []))
        context_aware_queries.extend(context_aware_results.get('statement', []))
        
        print(f"   ✅ Context-aware generator produced {len(context_aware_queries)} DRHP-specific queries")
        print(f"      - Financial: {len(context_aware_results.get('financial', []))}")
        print(f"      - Operational: {len(context_aware_results.get('operational', []))}")
        print(f"      - Cross-Reference: {len(context_aware_results.get('cross_reference', []))}")
        print(f"      - Statement: {len(context_aware_results.get('statement', []))}")
        
        # Merge all queries
        all_queries = nse_queries + advanced_queries + context_aware_queries
        
        print(f"\n   📊 Total queries after context-aware generation: {len(all_queries)}")
        
        # ====================================================================
        # STEP 7: FORMAT OUTPUT
        # ====================================================================
        
        elapsed_time = time.time() - start_time
        
        print(f"\n{'='*80}")
        print(f"✅ NSE-GRADE COMPLIANCE CHECK COMPLETE (CONTENT-AWARE)")
        print(f"{'='*80}")
        print(f"   Processing Time: {elapsed_time:.1f}s")
        print(f"   Internal Checks: {internal_stats['total_checked']} applicable")
        print(f"   Base NSE Queries: {len(nse_queries)}")
        print(f"   Advanced Queries: {len(advanced_queries)}")
        print(f"   Context-Aware Queries: {len(context_aware_queries)}")
        print(f"   Total Queries: {len(all_queries)}")
        print(f"   🎯 DRHP Context: {drhp_context['metadata']['products_count']} products, "
              f"{drhp_context['metadata']['anomalies_count']} anomalies detected")
        print(f"{'='*80}\n")
        
        # Structured output
        result = {
            "company_name": company_name,
            "drhp_chapter": drhp_chapter,
            "company_profile": company_profile,
            "ipo_structure": ipo_profile,
            "drhp_context": drhp_context,  # ✅ NEW - Extracted context
            # Whether the NSE Engine (Engine 3) had Gemini enabled during this run
            "nse_engine_gemini_enabled": getattr(self, 'nse_engine_gemini_enabled', False),
            "nse_queries": all_queries,  # ✅ NOW INCLUDES ALL QUERIES
            "base_queries": len(nse_queries),
            "advanced_queries": len(advanced_queries),
            "context_aware_queries": len(context_aware_queries),  # ✅ NEW
            "advanced_breakdown": {
                "contradictions": len(advanced_results.get('contradictions', [])),
                "entity_identity": len(advanced_results.get('entity_identity', [])),
                "purpose_interrogation": len(advanced_results.get('purpose_interrogation', [])),
                "hygiene": len(advanced_results.get('hygiene', []))
            },
            "context_aware_breakdown": {  # ✅ NEW
                "financial": len(context_aware_results.get('financial', [])),
                "operational": len(context_aware_results.get('operational', [])),
                "cross_reference": len(context_aware_results.get('cross_reference', [])),
                "statement": len(context_aware_results.get('statement', []))
            },
            "total_queries": len(nse_queries),
            "internal_checks_run": run_internal_checks,
            "internal_stats": internal_stats,
            "processing_time_seconds": round(elapsed_time, 2)
        }
        
        # Add formatted text output if requested
        if output_format == "nse_text":
            result["nse_formatted_output"] = format_nse_section(drhp_chapter, nse_queries)
        
        return result
    
    # ========================================================================
    # SYSTEM A: INTERNAL COMPLIANCE CHECKS (SILENT)
    # ========================================================================
    
    def _run_internal_compliance_checks(
        self,
        document_chunks: List[Dict],
        drhp_chapter: str,
        chapter_filters: List[str],
        mandatory_only: bool,
        initial_limit: int,
        ipo_profile: Dict[str, bool]  # ✅ NEW: IPO structure for filtering
    ) -> Dict[str, int]:
        """
        Run internal compliance checks (System A)
        
        This runs SILENTLY - no user-facing output
        Purpose: Internal validation, audit trail, merchant banker checks
        
        Args:
            document_chunks: DRHP chunks
            drhp_chapter: Chapter name
            chapter_filters: Neo4j chapters to check
            mandatory_only: Only mandatory obligations
            initial_limit: Max obligations per chapter
            ipo_profile: IPO structure (for applicability filtering)
        
        Returns:
            Statistics dict (for logging only)
        """
        
        total_checked = 0
        total_skipped = 0
        
        if not self.semantic_search:
            return {'total_checked': 0, 'total_skipped': 0}
        
        for chapter in chapter_filters:
            # Retrieve obligations from Neo4j
            obligations = self.semantic_search.get_obligations_by_chapter(
                chapter=chapter,
                mandatory_only=mandatory_only,
                limit=initial_limit
            )
            
            for obligation in obligations:
                obligation_category = obligation.get('category', '').lower()
                
                # ✅ APPLICABILITY FILTERING (KEY FIX)
                # Check if this obligation is applicable to this IPO
                if not self._is_obligation_applicable(obligation_category, ipo_profile):
                    total_skipped += 1
                    continue  # Skip non-applicable obligations
                
                # Process applicable obligation
                total_checked += 1
                
                state = create_initial_state(
                    requirement=obligation["requirement_text"],
                    drhp_chapter=drhp_chapter,
                    user_document_chunks=document_chunks,
                    regulation_type=self.regulation_type
                )
                
                # Safe metadata attachment
                state.obligation_id = obligation.get("obligation_id")
                state.source_clause = obligation.get("source_clause")
                state.mandatory = obligation.get("mandatory", False)
                
                # Run agents
                state = self.retrieval_agent.execute(state)
                state = self.analysis_agent.execute(state)
                state = self.validation_agent.execute(state)
                
                if state.needs_reanalysis and state.reanalysis_count < 1:
                    state = self.reanalysis_agent.execute(state)
                
                _ = self.synthesis_agent.execute(state)
                
                # ⚠️ INTENTIONALLY NO RETURN OR STORAGE
                # Results are used for internal validation only
        
        return {
            'total_checked': total_checked,
            'total_skipped': total_skipped
        }
    
    def _is_obligation_applicable(
        self,
        obligation_category: str,
        ipo_profile: Dict[str, bool]
    ) -> bool:
        """
        Check if obligation is applicable to this IPO
        
        This prevents checking irrelevant obligations like:
        - Convertible debt rules (if no debt)
        - Warrant rules (if no warrants)
        - VC lock-in rules (if no VC investors)
        
        Args:
            obligation_category: Obligation category/description
            ipo_profile: IPO structure from applicability engine
        
        Returns:
            True if obligation should be checked
        """
        
        category_lower = obligation_category.lower()
        
        # Debt-related obligations
        if any(word in category_lower for word in ["debenture", "convertible debt", "ncd", "bond"]):
            return ipo_profile.get("has_convertible_debt", True)
        
        # Warrant obligations
        if "warrant" in category_lower:
            return ipo_profile.get("has_warrants", True)
        
        # Secured instrument obligations
        if any(word in category_lower for word in ["security", "charge", "mortgage", "pledge", "hypothecation"]):
            return ipo_profile.get("has_secured_instruments", True)
        
        # SR shares obligations
        if any(word in category_lower for word in ["sr equity", "superior voting", "differential voting"]):
            return ipo_profile.get("has_sr_shares", True)
        
        # VC/PE lock-in obligations
        if any(word in category_lower for word in ["venture capital", "aif", "fvci", "private equity"]):
            return ipo_profile.get("has_vc_or_pe", True)
        
        # Employee equity obligations
        if any(word in category_lower for word in ["esop", "employee stock", "sweat equity"]):
            return ipo_profile.get("has_employee_equity", True)
        
        # Default: check the obligation (applicable to all IPOs)
        return True
    
    # ========================================================================
    # SYSTEM B: NSE CONTENT REVIEW (USER-VISIBLE)
    # ========================================================================
    
    def _run_nse_content_review(
        self,
        document_chunks: List[Dict],
        company_name: str,
        company_profile: Dict[str, Any],
        ipo_profile: Dict[str, bool],
        drhp_file_path: str = None  # ✅ ADDED for PDF path
    ) -> List[Dict[str, Any]]:
        """
        Generate NSE-style content queries (System B)
        
        This is the ONLY user-visible output
        
        Args:
            document_chunks: DRHP chunks
            company_name: Extracted company name
            company_profile: Revenue, employees, business type
            ipo_profile: IPO structure (for additional filtering)
            drhp_file_path: Path to original PDF (for page extraction)
        
        Returns:
            List of NSE-style queries
        """
        
        # Check if chapter has business content
        if not self._contains_business_content(document_chunks):
            print(f"   ℹ️  No business content detected - skipping NSE review")
            return []
        
        # Generate NSE queries (Enhanced with SystemB for accurate page extraction)
        nse_queries = self.content_review_agent.analyze_business_chapter(
            drhp_chunks=document_chunks,
            company_name=company_name,
            company_profile=company_profile,
            pdf_path=drhp_file_path,  # ✅ ADDED - enables Engine 1 page extraction
            chapter_name="Business Overview"  # ✅ ADDED - enables chapter-specific rules
        )

        # Capture whether the underlying Engine 3 used Gemini (for audit/logging)
        try:
            self.nse_engine_gemini_enabled = getattr(self.content_review_agent, 'last_gemini_enabled', False)
        except Exception:
            self.nse_engine_gemini_enabled = False
        
        # ✅ ADDITIONAL FILTERING: Remove non-applicable NSE queries
        # (e.g., if NSE agent asks about debt but IPO has no debt)
        filtered_queries = []
        for query in nse_queries:
            query_category = query.get('category', '')
            
            if self.applicability_engine.is_query_applicable(query_category, ipo_profile):
                filtered_queries.append(query)
        
        if len(nse_queries) != len(filtered_queries):
            print(f"   🔍 Filtered {len(nse_queries) - len(filtered_queries)} non-applicable NSE queries")
        
        return filtered_queries
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _contains_business_content(self, chunks: List[Dict]) -> bool:
        """
        Detect if chunks contain business-related content
        
        Uses content signals (not chapter name)
        """
        import re
        
        # Scan up to 50 chunks (business content might start late)
        sample_size = min(50, len(chunks))
        sample_text = "\n".join([c.get("text", "") for c in chunks[:sample_size]])
        
        # Business content signals
        business_signals = [
            r"\brevenue\b",
            r"\bcustomer\b",
            r"\bdealer\b",
            r"\blogistics\b",
            r"\battrition\b",
            r"\bprocurement\b",
            r"\bquality\b",
            r"\binsurance\b",
            r"\boperations\b",
            r"\bmanufacturing\b",
            r"\bsales\b",
            r"\bmarketing\b"
        ]
        
        # Count matches
        matches = sum(
            1 for signal in business_signals
            if re.search(signal, sample_text, re.IGNORECASE)
        )
        
        # Need at least 3 business signals
        return matches >= 3
    
    def _extract_company_name(self, chunks: List[Dict]) -> str:
        """Extract company name from first few chunks"""
        import re
        
        text = "\n".join([c.get("text", "") for c in chunks[:5]])
        
        # Look for "XXX Limited" pattern
        match = re.search(
            r"([A-Z][A-Za-z\s&]+(?:Limited|Private Limited|Pvt\.?\s*Ltd\.?|Ltd\.?))",
            text
        )
        
        return match.group(1) if match else "the Company"
    
    def _extract_company_profile(self, chunks: List[Dict]) -> Dict[str, Any]:
        """
        Extract company profile for severity escalation
        
        Extracts:
        - Revenue (₹ crores)
        - Employee count
        - Business type
        """
        import re
        
        # Sample first 30 chunks
        text = "\n".join([c.get("text", "") for c in chunks[:30]])
        
        # Extract revenue (₹ crores)
        revenue = 0
        revenue_matches = re.findall(r"₹[\s\d,]+\.?\d*\s*crore", text, re.IGNORECASE)
        
        if revenue_matches:
            try:
                amounts = []
                for match in revenue_matches:
                    num = re.search(r"[\d,]+\.?\d*", match)
                    if num:
                        amounts.append(float(num.group(0).replace(",", "")))
                if amounts:
                    revenue = max(amounts)
            except:
                revenue = 0
        
        # Extract employee count
        employees = 0
        employee_matches = re.findall(
            r"(\d+)\s*(?:employee|staff|workforce)",
            text,
            re.IGNORECASE
        )
        
        if employee_matches:
            try:
                employees = max([int(m) for m in employee_matches])
            except:
                employees = 0
        
        # Detect business type
        business_type = ""
        type_patterns = {
            "automotive": r"automotive|vehicle|automobile",
            "manufacturing": r"manufacturing|factory|plant|production",
            "technology": r"software|technology|IT|digital|tech",
            "pharma": r"pharmaceutical|pharma|drug|medicine",
            "services": r"services|consulting|advisory"
        }
        
        for btype, pattern in type_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                business_type = btype
                break
        
        return {
            "revenue": revenue,
            "employees": employees,
            "business_type": business_type
        }
    
    def _prepare_pages_dict(self, chunks: List[Dict]) -> Dict[int, str]:
        """
        Prepare pages dictionary for advanced intelligence layers
        
        Args:
            chunks: Document chunks from document processor
        
        Returns:
            {page_number: page_text} dictionary
        """
        pages_dict = {}

        for chunk in chunks:
            # Accept both 'page' (legacy) and 'page_number' (current) keys
            page_num = chunk.get('page') or chunk.get('page_number') or 0
            text = chunk.get('text', '') or ''

            if page_num > 0:
                if page_num in pages_dict:
                    # Append to existing page text
                    pages_dict[page_num] += "\n" + text
                else:
                    pages_dict[page_num] = text
            else:
                # Debug: warn about chunk missing page info (shouldn't happen)
                if text.strip():
                    print(f"   ⚠️  Skipping chunk without page number; text preview: {text[:80]!r}")

        # Debug: report prepared pages count
        print(f"   ✅ Prepared pages dict with {len(pages_dict)} pages")

        return pages_dict


def get_multi_agent_orchestrator(regulation_type: str = "ICDR"):
    """Factory function for orchestrator"""
    return MultiAgentComplianceOrchestrator(regulation_type)