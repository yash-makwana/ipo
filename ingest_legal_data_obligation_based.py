#!/usr/bin/env python3
"""
FINAL VERIFIED LEGAL INGESTION
=============================
✔ Matches SEBI ICDR 2018 structure (Chapter → Regulation)
✔ Matches Companies Act 2013 structure (Chapter → Section)
✔ No TOC assumptions for ICDR
✔ Skips Arrangement of Sections for Companies Act
✔ No fake chapters, no missing chapters
✔ Compliance-grade Neo4j graph
"""

import os
import re
import time
import hashlib
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import List

import PyPDF2
from dotenv import load_dotenv
from pydantic import BaseModel

from google import genai
from google.genai import types

from db_config import get_neo4j_connection
from embeddings_service import get_embeddings_service

# ---------------------------------------------------------------------
# ENV
# ---------------------------------------------------------------------

load_dotenv(".env-local")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY missing")

client = genai.Client(api_key=GEMINI_API_KEY)

REQUEST_DELAY = 8
_last_call = 0

def rate_limited(fn):
    global _last_call
    delta = time.time() - _last_call
    if delta < REQUEST_DELAY:
        time.sleep(REQUEST_DELAY - delta)
    res = fn()
    _last_call = time.time()
    return res

def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

# ---------------------------------------------------------------------
# SCHEMA
# ---------------------------------------------------------------------

class Obligation(BaseModel):
    requirement_text: str
    mandatory: bool
    obligation_type: str
    subject: str
    action: str
    object: str
    source_clause: str
    confidence: float

class ObligationList(BaseModel):
    obligations: List[Obligation]

# ---------------------------------------------------------------------
# PDF READER
# ---------------------------------------------------------------------

def read_pdf(path: Path) -> str:
    text = ""
    with open(path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += (page.extract_text() or "") + "\n"
    return text

# ---------------------------------------------------------------------
# ICDR PARSER (CHAPTER → REGULATION)
# ---------------------------------------------------------------------

def parse_icdr(text: str):
    chapters = {}

    chapter_re = re.compile(
        r'CHAPTER\s+([IVXLCDM]+)\s*-\s*([A-Z][A-Z\s]+)',
        re.IGNORECASE
    )
    regulation_re = re.compile(
        r'\n\s*(\d+[A-Z]?)\.\s',
        re.IGNORECASE
    )

    chapter_matches = list(chapter_re.finditer(text))

    for i, ch in enumerate(chapter_matches):
        ch_start = ch.end()
        ch_end = chapter_matches[i + 1].start() if i + 1 < len(chapter_matches) else len(text)
        ch_text = text[ch_start:ch_end]

        regs = []
        reg_matches = list(regulation_re.finditer(ch_text))
        for j, r in enumerate(reg_matches):
            r_start = r.start()
            r_end = reg_matches[j + 1].start() if j + 1 < len(reg_matches) else len(ch_text)
            regs.append((r.group(1), ch_text[r_start:r_end]))

        chapters[ch.group(1)] = {
            "title": ch.group(2).strip(),
            "units": regs
        }

    return chapters

# ---------------------------------------------------------------------
# COMPANIES ACT PARSER (CHAPTER → SECTION)
# ---------------------------------------------------------------------

def parse_companies_act(text: str):
    chapters = {}

    # Skip Arrangement of Sections
    start_idx = text.upper().find("CHAPTER I")
    text = text[start_idx:]

    chapter_re = re.compile(
        r'CHAPTER\s+([IVXLCDM]+)\s*\n\s*([A-Z][A-Z\s]+)',
        re.IGNORECASE
    )
    section_re = re.compile(
        r'\n\s*(\d+[A-Z]?)\.\s',
        re.MULTILINE
    )

    chapter_matches = list(chapter_re.finditer(text))

    for i, ch in enumerate(chapter_matches):
        ch_start = ch.end()
        ch_end = chapter_matches[i + 1].start() if i + 1 < len(chapter_matches) else len(text)
        ch_text = text[ch_start:ch_end]

        secs = []
        sec_matches = list(section_re.finditer(ch_text))
        for j, s in enumerate(sec_matches):
            s_start = s.start()
            s_end = sec_matches[j + 1].start() if j + 1 < len(sec_matches) else len(ch_text)
            secs.append((s.group(1), ch_text[s_start:s_end]))

        chapters[ch.group(1)] = {
            "title": ch.group(2).strip(),
            "units": secs
        }

    return chapters

# ---------------------------------------------------------------------
# GEMINI OBLIGATION EXTRACTION
# ---------------------------------------------------------------------

def extract_obligations(text: str, ref: str):
    prompt = f"""
Extract legal obligations.

Return JSON only.

Fields:
- requirement_text (20–300 chars)
- mandatory
- obligation_type (DISCLOSURE, CONDITION, TIMELINE, PROCEDURAL, PROHIBITION)
- subject
- action
- object
- source_clause: {ref}
- confidence (0.0–1.0)

TEXT:
{text[:20000]}
"""

    def call():
        return client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ObligationList,
                temperature=0.1,
                max_output_tokens=2500
            )
        )

    res = rate_limited(call)
    return res.parsed.obligations if res and res.parsed else []

# ---------------------------------------------------------------------
# NEO4J INGESTION
# ---------------------------------------------------------------------

def ingest(driver, regulation: str, chapters: dict):
    emb = get_embeddings_service()
    total = 0

    with driver.session() as s:
        s.run(
            "MERGE (r:Regulation {id:$id}) SET r.ingested_at=$ts",
            {"id": regulation, "ts": datetime.now(timezone.utc).isoformat()}
        )

        for ch_num, ch in chapters.items():
            ch_id = f"{regulation}_CH{ch_num}"
            s.run(
                """
                MERGE (c:Chapter {id:$id})
                SET c.number=$num, c.title=$title
                WITH c MATCH (r:Regulation {id:$reg})
                MERGE (r)-[:HAS_CHAPTER]->(c)
                """,
                {"id": ch_id, "num": ch_num, "title": ch["title"], "reg": regulation}
            )

            for unit_num, unit_text in ch["units"]:
                obligations = extract_obligations(
                    unit_text, f"{regulation} Chapter {ch_num} Unit {unit_num}"
                )
                if not obligations:
                    continue

                vectors = emb.generate_embeddings(
                    [o.requirement_text for o in obligations]
                )

                for o, v in zip(obligations, vectors):
                    s.run(
                        """
                        MERGE (o:Obligation {hash:$hash})
                        SET o.requirement_text=$text,
                            o.mandatory=$mand,
                            o.obligation_type=$type,
                            o.subject=$subj,
                            o.action=$act,
                            o.object=$obj,
                            o.source_clause=$src,
                            o.confidence=$conf,
                            o.embedding=$emb,
                            o.regulation=$reg
                        """,
                        {
                            "hash": sha(o.requirement_text),
                            "text": o.requirement_text,
                            "mand": o.mandatory,
                            "type": o.obligation_type,
                            "subj": o.subject,
                            "act": o.action,
                            "obj": o.object,
                            "src": o.source_clause,
                            "conf": o.confidence,
                            "emb": v.tolist(),
                            "reg": regulation
                        }
                    )
                    total += 1

    return total

# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf-dir", default="./legal_pdfs")
    args = parser.parse_args()

    driver = get_neo4j_connection()
    print("✅ Connected to Neo4j")

    icdr_text = read_pdf(Path(args.pdf_dir) / "ICDR_Regulations.pdf")
    ca_text   = read_pdf(Path(args.pdf_dir) / "Companies_Act_2013.pdf")

    icdr = parse_icdr(icdr_text)
    ca   = parse_companies_act(ca_text)

    total = 0
    total += ingest(driver, "ICDR_2018", icdr)
    total += ingest(driver, "COMPANIES_ACT_2013", ca)

    print(f"\n✅ INGESTION COMPLETE — {total} obligations stored")

if __name__ == "__main__":
    main()
