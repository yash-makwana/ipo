"""
Compliance Engine - FINAL PRODUCTION VERSION
============================================
Fixes:
1. Model selection that actually works
2. Proper page number extraction and display
3. Correct regulation filtering
"""

from semantic_legal_search import get_semantic_search
from embeddings_service import get_embeddings_service
from reranking_service import get_reranking_service
import pdfplumber
from pathlib import Path
import json
import time
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import os
from google import genai
from google.genai import types
import re

load_dotenv('.env-local')
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


class ComplianceEngine:
    """Compliance Engine - Production Ready"""
    
    def __init__(self, regulation_type="ICDR"):
        """Initialize Compliance Engine"""
        self.regulation_type = regulation_type
        self.search = get_semantic_search(regulation_type)
        self.embeddings = get_embeddings_service()
        self.reranker = get_reranking_service()
        
        # Initialize Gemini
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        
        # ✅ FIX 1: PROPER MODEL SELECTION
        # Don't use models.get() - just try generate_content with a test prompt
        models_to_try = [
            "gemini-2.5-flash-lite",   # 4K RPM - BEST
            "gemini-2.0-flash-lite",   # 4K RPM
            "gemini-2.0-flash",        # 2K RPM
            "gemini-2.5-flash",        # 1K RPM
        ]
        
        self.model_name = None
        print(f"\n🔍 Testing models for availability...")
        
        for model in models_to_try:
            try:
                print(f"   Testing {model}...", end=" ")
                # ✅ Actually test the model by making a tiny request
                test_response = self.client.models.generate_content(
                    model=model,
                    contents="Test",
                    config=types.GenerateContentConfig(
                        temperature=0.1,
                        max_output_tokens=10,
                    )
                )
                self.model_name = model
                print(f"✅ AVAILABLE")
                break
            except Exception as e:
                error_str = str(e)
                if "404" in error_str or "not found" in error_str.lower():
                    print(f"❌ Not found")
                elif "429" in error_str or "quota" in error_str.lower():
                    print(f"⚠️  Available but quota exceeded")
                    # Still set this as the model - it exists, just rate limited
                    self.model_name = model
                    break
                else:
                    print(f"❌ Error: {error_str[:50]}")
                continue
        
        if not self.model_name:
            raise Exception("❌ No Gemini models available! Check your API key.")
        
        # Rate limiting config
        self.requests_per_minute = 50
        self.min_delay_between_requests = 1.5
        self.last_request_time = 0
        self.request_count = 0
        self.request_window_start = time.time()
        self.consecutive_errors = 0
        
        print(f"\n✅ ComplianceEngine initialized")
        print(f"   Regulation: {regulation_type}")
        print(f"   Model: {self.model_name}")
        print(f"   Rate Limit: {self.requests_per_minute} req/min")
        print(f"   Min Delay: {self.min_delay_between_requests}s\n")
    
    def rate_limit(self):
        """Aggressive rate limiting with exponential backoff"""
        current_time = time.time()
        
        # Reset counter if window expired
        if current_time - self.request_window_start >= 60:
            self.request_count = 0
            self.request_window_start = current_time
            if self.consecutive_errors > 0:
                self.consecutive_errors = 0
        
        # If at limit, wait
        if self.request_count >= self.requests_per_minute:
            wait_time = 60 - (current_time - self.request_window_start)
            if wait_time > 0:
                print(f"   ⏳ Rate limit. Waiting {wait_time:.1f}s...")
                time.sleep(wait_time + 2)
                self.request_count = 0
                self.request_window_start = time.time()
        
        # Exponential backoff for consecutive errors
        if self.consecutive_errors > 0:
            backoff_delay = min(2 ** self.consecutive_errors, 30)
            print(f"   ⏸️  Backoff {backoff_delay}s (errors: {self.consecutive_errors})")
            time.sleep(backoff_delay)
        
        # Minimum delay
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_delay_between_requests:
            time.sleep(self.min_delay_between_requests - time_since_last)
        
        self.request_count += 1
        self.last_request_time = time.time()

    def process_user_document(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract text from DRHP PDF - HANDLES MULTI-COLUMN LAYOUTS
        
        Args:
            file_path: Path to PDF file
        
        Returns:
            List of page chunks with text and page numbers
        """
        print(f"\n{'='*60}")
        print(f"📄 PROCESSING DOCUMENT (pdfplumber)")
        print(f"{'='*60}")
        print(f"   File: {file_path}")
        
        try:
            chunks = []
            pages_with_no_text = []
            
            # ✅ Use pdfplumber instead of PyPDF2
            with pdfplumber.open(file_path) as pdf:
                total_pages = len(pdf.pages)
                print(f"   Total Pages: {total_pages}")
                
                for i, page in enumerate(pdf.pages):
                    # ✅ Extract text (handles columns properly!)
                    text = page.extract_text()
                    
                    # Check if page has meaningful text
                    if not text or len(text.strip()) < 100:
                        pages_with_no_text.append(i + 1)
                        continue
                    
                    # ✅ Also extract tables (BONUS!)
                    tables = page.extract_tables()
                    
                    # Combine text and tables
                    full_text = text.strip()
                    
                    if tables:
                        table_text = "\n\nTABLES:\n"
                        for table in tables:
                            if table:
                                # Convert table to text
                                for row in table:
                                    if row:
                                        row_text = " | ".join([str(cell) if cell else "" for cell in row])
                                        table_text += row_text + "\n"
                        full_text += table_text
                    
                    chunks.append({
                        "page": i + 1,
                        "page_number": i + 1,  # Both fields for compatibility
                        "text": full_text,
                        "has_tables": len(tables) > 0
                    })
                
                print(f"   ✅ Extracted: {len(chunks)} pages with text")
                
                if pages_with_no_text:
                    print(f"   ⚠️  Pages with no/little text: {pages_with_no_text[:10]}")
                    if len(pages_with_no_text) > total_pages * 0.3:
                        print(f"   ⚠️  WARNING: {len(pages_with_no_text)} pages have no text")
                
                # ✅ DEBUG: Show sample extraction
                if chunks:
                    print(f"\n   📋 Sample from Page 1:")
                    print(f"   {chunks[0]['text'][:200]}...")
                
                print(f"{'='*60}\n")
                return chunks
                
        except Exception as e:
            print(f"❌ Error processing document: {e}")
            import traceback
            traceback.print_exc()
            return []

    def find_evidence(
        self, 
        chunks: List[Dict], 
        obligation_text: str, 
        top_k: int = 5
    ) -> List[Dict]:
        """Find evidence using semantic similarity"""
        if not chunks:
            print(f"      ⚠️  No chunks to search")
            return []
        
        try:
            texts = [c["text"] for c in chunks]
            emb_chunks = self.embeddings.generate_embeddings(texts)
            emb_query = self.embeddings.generate_single_embedding(obligation_text)

            scores = []
            for i, emb in enumerate(emb_chunks):
                score = float(
                    (emb_query @ emb) /
                    ((sum(emb_query**2)**0.5) * (sum(emb**2)**0.5) + 1e-9)
                )
                scores.append((score, i))

            scores.sort(reverse=True)
            top = scores[:top_k]

            results = []
            for score, idx in top:
                if score > 0.15:  # Threshold
                    results.append({
                        "page": chunks[idx]["page"],
                        "text": chunks[idx]["text"][:800],
                        "similarity_score": score
                    })
            
            # ✅ FIX 2: DEBUG PAGE EXTRACTION
            if results:
                pages = [r["page"] for r in results]
                print(f"      🔍 Found evidence on pages: {pages} (scores: {[f'{r['similarity_score']:.2f}' for r in results]})")
            else:
                print(f"      ⚠️  No evidence found (all scores < 0.15)")
            
            return results
            
        except Exception as e:
            print(f"      ❌ Error finding evidence: {e}")
            return []

    def check_obligation(
        self, 
        obligation: Dict[str, Any], 
        chunks: List[Dict]
    ) -> Dict[str, Any]:
        """Check if obligation is met"""
        # Rate limit
        self.rate_limit()
        
        # ✅ FIX 2: EXTRACT PAGES FIRST (before API call)
        evidence = self.find_evidence(chunks, obligation["requirement_text"])
        
        pages = []
        if evidence:
            pages = sorted(list(set([e["page"] for e in evidence if e.get("page")])))
            print(f"      ✅ Pages extracted: {pages}")
        else:
            print(f"      ⚠️  No pages found (no evidence)")
        
        evidence_text = ""
        if evidence:
            best_evidence = evidence[0]
            evidence_text = best_evidence.get("text", "")[:600]

        # Build prompt
        prompt = f"""You are a SEBI/Companies Act compliance expert.

LEGAL OBLIGATION:
{obligation["requirement_text"]}

SOURCE:
Citation: {obligation["citation"]}
Chapter: {obligation.get("chapter", "N/A")}

USER'S DRHP (Pages: {pages if pages else "None"}):
{json.dumps([{
    "page": e["page"], 
    "text": e["text"][:350],
    "score": f"{e['similarity_score']:.2f}"
} for e in evidence], indent=2) if evidence else "No relevant content found"}

STATUS: PRESENT|INSUFFICIENT|MISSING|UNCLEAR

JSON response (no markdown):
{{
  "status": "...",
  "explanation": "...",
  "evidence": "...",
  "missing_details": "...",
  "confidence": 0.0-1.0
}}"""

        try:
            # ✅ API CALL WITH RETRY
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    response = self.client.models.generate_content(
                        model=self.model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            temperature=0.1,
                            max_output_tokens=2000,
                        )
                    )
                    
                    # SUCCESS
                    self.consecutive_errors = 0
                    
                    text = response.text.strip()
                    
                    # Clean JSON
                    if '```json' in text:
                        text = text.split('```json')[1].split('```')[0]
                    elif '```' in text:
                        text = text.split('```')[1].split('```')[0]
                    
                    result = json.loads(text.strip())
                    
                    # ✅ FIX 2: ADD PAGES (already extracted above)
                    result['obligation_text'] = obligation["requirement_text"]
                    result['citation'] = obligation["citation"]
                    result['source_clause'] = obligation.get("source_clause", obligation["citation"])
                    result['chapter'] = obligation.get("chapter")
                    result['mandatory'] = obligation.get("mandatory", False)
                    result['obligation_type'] = obligation.get("obligation_type")
                    result['pages'] = pages  # ✅ From evidence search, NOT LLM
                    
                    # Fill evidence if missing
                    if not result.get('evidence') or not result['evidence'].strip():
                        if evidence_text and result['status'] in ['PRESENT', 'INSUFFICIENT']:
                            result['evidence'] = evidence_text
                    
                    # Clean missing_details
                    if result.get('missing_details'):
                        missing = result['missing_details']
                        if isinstance(missing, str):
                            missing = missing.replace('.,', ',').replace('..', '.')
                            parts = [p.strip() for p in missing.split(',')]
                            result['missing_details'] = ', '.join(p for p in parts if p and len(p) > 3)
                    
                    # Ensure confidence is float
                    try:
                        result['confidence'] = float(result.get('confidence', 0.5))
                    except:
                        result['confidence'] = 0.5
                    
                    print(f"      ✅ Analysis complete (pages: {pages})")
                    return result
                    
                except Exception as api_error:
                    error_str = str(api_error)
                    
                    # Check if rate limit
                    if '429' in error_str or 'RESOURCE_EXHAUSTED' in error_str or 'quota' in error_str.lower():
                        retry_count += 1
                        self.consecutive_errors += 1
                        
                        if retry_count < max_retries:
                            wait_time = min(2 ** (retry_count + self.consecutive_errors), 60)
                            print(f"      ⚠️  429 error. Retry {retry_count}/{max_retries} after {wait_time}s")
                            time.sleep(wait_time)
                            continue
                        else:
                            print(f"      ❌ Max retries reached")
                            # ✅ FIX 2: RETURN PAGES EVEN ON ERROR
                            return self._create_error_result(obligation, pages, "Rate limit exceeded after retries")
                    else:
                        raise api_error
            
        except json.JSONDecodeError as e:
            print(f"      ❌ JSON error: {e}")
            return self._create_error_result(obligation, pages, "JSON parse error")
            
        except Exception as e:
            error_msg = str(e)
            print(f"      ❌ Error: {error_msg[:100]}")
            self.consecutive_errors += 1
            return self._create_error_result(obligation, pages, error_msg)
    
    def _create_error_result(
        self, 
        obligation: Dict[str, Any], 
        pages: List[int], 
        error_msg: str
    ) -> Dict[str, Any]:
        """Create error result - PRESERVES PAGES"""
        # Shorten error
        if len(error_msg) > 200:
            error_msg = error_msg[:200] + "..."
        
        print(f"      📄 Error result created with pages: {pages}")
        
        return {
            "status": "UNCLEAR",
            "explanation": f"Analysis error: {error_msg}",
            "evidence": "",
            "missing_details": "",
            "confidence": 0.0,
            "pages": pages,  # ✅ FIX 2: PAGES PRESERVED!
            "obligation_text": obligation["requirement_text"],
            "citation": obligation["citation"],
            "source_clause": obligation.get("source_clause", obligation["citation"]),
            "chapter": obligation.get("chapter"),
            "mandatory": obligation.get("mandatory", False),
            "obligation_type": obligation.get("obligation_type")
        }

    def check_drhp_compliance(
        self, 
        file_path: str, 
        mapping: Dict[str, Any],
        use_table_extraction: bool = False
    ) -> Dict[str, Any]:
        """Main compliance check entry point"""
        start = time.time()
        
        # Process document
        chunks = self.process_user_document(file_path)
        if not chunks:
            return {
                "error": "Could not process document",
                "items": [],
                "total_requirements": 0
            }

        # ✅ FIX 3: GET OBLIGATIONS FOR SELECTED REGULATION ONLY
        filters = mapping.get("neo4j_filters", {}).get(self.regulation_type, {})
        chapters = filters.get("chapters", [])
        mandatory_only = filters.get("mandatory_only", False)

        print(f"\n{'='*60}")
        print(f"🔍 FETCHING OBLIGATIONS")
        print(f"{'='*60}")
        print(f"   Regulation: {self.regulation_type}")  # ✅ Shows which regulation
        print(f"   Chapters: {chapters}")
        print(f"   Mandatory only: {mandatory_only}")
        
        if not chapters:
            print(f"\n⚠️  WARNING: No chapters configured for {self.regulation_type}")
            print(f"   Check your drhp_mapping.py file")
            return {
                "error": f"No chapters configured for {self.regulation_type} in drhp_mapping.py",
                "items": [],
                "total_requirements": 0
            }
        
        all_obligations = []
        for chapter in chapters:
            print(f"\n   Fetching {self.regulation_type} {chapter}...")
            obligations = self.search.get_obligations_by_chapter(
                chapter=chapter,
                mandatory_only=mandatory_only,
                limit=200
            )
            all_obligations.extend(obligations)
            print(f"   ✅ Found {len(obligations)} obligations")
        
        print(f"\n{'='*60}")
        print(f"📊 TOTAL: {len(all_obligations)} {self.regulation_type} obligations")
        print(f"⏱️  Est: {len(all_obligations) * 2 / 60:.1f} min")
        print(f"{'='*60}\n")

        if not all_obligations:
            return {
                "error": f"No {self.regulation_type} obligations found for chapters: {chapters}",
                "items": [],
                "total_requirements": 0
            }

        # Check each
        results = []
        for i, obligation in enumerate(all_obligations, 1):
            citation = obligation.get('citation', 'Unknown')
            print(f"\n[{i}/{len(all_obligations)}] {citation}")
            
            verdict = self.check_obligation(obligation, chunks)
            results.append(verdict)
            
            status_icon = {
                "PRESENT": "✅",
                "INSUFFICIENT": "⚠️",
                "MISSING": "❌",
                "UNCLEAR": "❓"
            }.get(verdict["status"], "❓")
            
            # ✅ FIX 2: SHOW PAGES IN LOG
            pages_display = verdict.get('pages', [])
            print(f"   {status_icon} {verdict['status']} | Pages: {pages_display if pages_display else 'None'}")

        # Aggregate
        summary = {
            "PRESENT": len([r for r in results if r["status"] == "PRESENT"]),
            "INSUFFICIENT": len([r for r in results if r["status"] == "INSUFFICIENT"]),
            "MISSING": len([r for r in results if r["status"] == "MISSING"]),
            "UNCLEAR": len([r for r in results if r["status"] == "UNCLEAR"])
        }
        
        priority_summary = {
            "CRITICAL": len([r for r in results if r["status"] == "MISSING" and r.get("mandatory")]),
            "HIGH": len([r for r in results if r["status"] == "INSUFFICIENT" and r.get("mandatory")]),
            "MEDIUM": len([r for r in results if r["status"] in ["INSUFFICIENT", "UNCLEAR"] and not r.get("mandatory")]),
            "LOW": len([r for r in results if r["status"] == "PRESENT"])
        }

        elapsed = time.time() - start
        
        print(f"\n{'='*60}")
        print(f"📊 COMPLETE")
        print(f"{'='*60}")
        print(f"   Regulation: {self.regulation_type}")  # ✅ Confirm regulation checked
        print(f"   ✅ Present: {summary['PRESENT']}")
        print(f"   ⚠️  Insufficient: {summary['INSUFFICIENT']}")
        print(f"   ❌ Missing: {summary['MISSING']}")
        print(f"   ❓ Unclear: {summary['UNCLEAR']}")
        print(f"   ⏱️  Time: {elapsed/60:.1f} min")
        print(f"{'='*60}\n")

        return {
            "items": results,
            "total_requirements": len(results),
            "summary": summary,
            "priority_summary": priority_summary,
            "processing_time_seconds": int(elapsed),
            "regulation_type": self.regulation_type,  # ✅ Returned to frontend
            "chapters_checked": chapters,
            "mandatory_only": mandatory_only,
            "document_pages_processed": len(chunks)
        }


def get_compliance_engine(regulation_type="ICDR"):
    """Factory function"""
    return ComplianceEngine(regulation_type)
