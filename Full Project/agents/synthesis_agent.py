"""
Synthesis Agent
==============
Responsible for generating the final compliance report

Responsibilities:
1. Aggregate all analysis results
2. Determine priority/severity
3. Generate actionable recommendations
4. Add legal citations
5. Format final output
"""

import time
from typing import Dict, Any, List
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from state_models import ComplianceState, SynthesisOutput, update_agent_path


class SynthesisAgent:
    """
    Synthesis Agent - Final Report Generation
    
    Responsibilities:
    1. Finalize status and explanation
    2. Determine priority level (CRITICAL/HIGH/MEDIUM/LOW)
    3. Extract legal citations
    4. Generate actionable recommendations
    5. Calculate total processing time
    """
    
    def __init__(self):
        """Initialize Synthesis Agent"""
        print(f"✅ SynthesisAgent initialized")
    
    def determine_priority(self, state: ComplianceState) -> str:
        """
        Determine priority level based on status and requirement
        
        Args:
            state: Current state
        
        Returns:
            Priority level (CRITICAL/HIGH/MEDIUM/LOW)
        """
        # Critical keywords
        critical_keywords = [
            'attrition', 'employee', 'director', 'KMP', 'ownership',
            'capacity', 'financial statement', 'auditor', 'fraud',
            'litigation', 'DIN', 'board meeting', 'independent director'
        ]
        
        # High priority keywords
        high_keywords = [
            'training', 'quality', 'procurement', 'distribution', 'sales',
            'committee', 'CSR', 'related party', 'capital structure',
            'shareholding', 'promoter'
        ]
        
        req_lower = state.requirement.lower()
        
        # MISSING items are always high/critical priority
        if state.status == 'MISSING':
            if any(kw in req_lower for kw in critical_keywords):
                return 'CRITICAL'
            return 'HIGH'
        
        # INSUFFICIENT items
        if state.status == 'INSUFFICIENT':
            if any(kw in req_lower for kw in critical_keywords):
                return 'HIGH'
            if any(kw in req_lower for kw in high_keywords):
                return 'MEDIUM'
            return 'LOW'
        
        # UNCLEAR items need attention
        if state.status == 'UNCLEAR':
            return 'MEDIUM'
        
        # PRESENT items are low priority (just need review)
        return 'LOW'
    
    def extract_legal_citations(self, state: ComplianceState) -> str:
        """
        Extract and format legal citations
        
        Args:
            state: Current state
        
        Returns:
            Formatted citation string
        """
        if not state.legal_requirements:
            return ""
        
        # Get top matching legal requirement
        top_legal = state.legal_requirements[0]
        
        # Build citation
        citation_parts = []
        
        if state.regulation_type == "ICDR":
            if top_legal.get('regulation_number'):
                citation_parts.append(f"ICDR Regulation {top_legal['regulation_number']}")
            if top_legal.get('chapter_number'):
                citation_parts.append(f"Chapter {top_legal['chapter_number']}")
        else:
            if top_legal.get('section_number'):
                citation_parts.append(f"Companies Act Section {top_legal['section_number']}")
            if top_legal.get('chapter_number'):
                citation_parts.append(f"Chapter {top_legal['chapter_number']}")
        
        # Add chunk ID for reference
        if top_legal.get('chunk_id'):
            citation_parts.append(f"({top_legal['chunk_id']})")
        
        return " | ".join(citation_parts) if citation_parts else "General Requirement"
    
    def generate_recommendations(self, state: ComplianceState) -> List[str]:
        """
        Generate actionable recommendations based on status
        
        Args:
            state: Current state
        
        Returns:
            List of recommendations
        """
        recommendations = []
        
        if state.status == "MISSING":
            recommendations.append(
                f"⚠️  IMMEDIATE ACTION: Add complete disclosure for: {state.requirement}"
            )
            if state.missing_details:
                recommendations.append(
                    f"📋 Required details: {state.missing_details}"
                )
            if state.legal_requirements:
                top_legal = state.legal_requirements[0]
                if top_legal.get('text'):
                    recommendations.append(
                        f"📚 Legal Reference: {top_legal['text'][:150]}..."
                    )
        
        elif state.status == "INSUFFICIENT":
            recommendations.append(
                f"⚠️  ENHANCE: Current disclosure is incomplete"
            )
            if state.missing_details:
                recommendations.append(
                    f"📋 Add the following: {state.missing_details}"
                )
            if state.pages:
                recommendations.append(
                    f"📄 Current content location: Pages {', '.join(map(str, state.pages))}"
                )
        
        elif state.status == "UNCLEAR":
            recommendations.append(
                f"🔍 REVIEW REQUIRED: Content is ambiguous"
            )
            recommendations.append(
                f"💡 Clarify the disclosure to explicitly address: {state.requirement}"
            )
            if state.missing_details:
                recommendations.append(
                    f"📋 Specific areas to clarify: {state.missing_details}"
                )
        
        elif state.status == "PRESENT":
            recommendations.append(
                f"✅ COMPLIANT: Requirement appears to be met"
            )
            if state.evidence:
                recommendations.append(
                    f"📄 Verified on pages: {', '.join(map(str, state.pages))}"
                )
            recommendations.append(
                f"🔍 Suggested: Final legal review for completeness"
            )
        
        return recommendations
    
    def execute(self, state: ComplianceState) -> ComplianceState:
        """
        Execute synthesis agent
        
        Args:
            state: Current state after all processing
        
        Returns:
            Final state with complete report
        """
        print(f"\n{'='*60}")
        print(f"📊 SYNTHESIS AGENT - FINAL REPORT")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        # Update agent path
        state = update_agent_path(state, "SYNTHESIS")
        
        # Finalize processing time
        if state.processing_start_time:
            state.processing_end_time = datetime.now()
            total_time = (state.processing_end_time - state.processing_start_time).total_seconds()
        else:
            total_time = 0.0
        
        # Determine priority
        state.priority = self.determine_priority(state)
        
        # Extract legal citations
        state.legal_citation = self.extract_legal_citations(state)
        
        # Generate recommendations
        state.recommendations = self.generate_recommendations(state)
        
        # Elapsed time for synthesis
        elapsed_ms = (time.time() - start_time) * 1000
        
        # Print final report
        print(f"\n{'='*60}")
        print(f"FINAL COMPLIANCE REPORT")
        print(f"{'='*60}")
        print(f"\n📋 Requirement:")
        print(f"   {state.requirement}")
        print(f"\n🎯 Status: {state.status}")
        print(f"🔥 Priority: {state.priority}")
        print(f"📊 Confidence: {state.confidence:.2f}")
        
        if state.pages:
            print(f"📄 Pages: {', '.join(map(str, state.pages))}")
        
        if state.legal_citation:
            print(f"📚 Legal Citation: {state.legal_citation}")
        
        print(f"\n💬 Explanation:")
        print(f"   {state.explanation}")
        
        if state.evidence:
            print(f"\n✅ Evidence:")
            print(f"   {state.evidence[:200]}...")
        
        if state.missing_details:
            print(f"\n⚠️  Missing Details:")
            print(f"   {state.missing_details[:200]}...")
        
        print(f"\n💡 Recommendations:")
        for i, rec in enumerate(state.recommendations, 1):
            print(f"   {i}. {rec}")
        
        print(f"\n⏱️  Processing:")
        print(f"   Agent Path: {' → '.join(state.agent_path)}")
        print(f"   Reanalysis Attempts: {state.reanalysis_count}")
        print(f"   Total Time: {total_time:.2f}s")
        print(f"   Synthesis Time: {elapsed_ms:.0f}ms")
        
        print(f"\n{'='*60}")
        
        return state


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """Test Synthesis Agent"""
    
    print("=" * 80)
    print("🧪 TESTING SYNTHESIS AGENT")
    print("=" * 80)
    
    from state_models import create_initial_state
    
    # Test Case 1: INSUFFICIENT status
    print("\n" + "="*80)
    print("TEST 1: INSUFFICIENT Status")
    print("="*80)
    
    state1 = create_initial_state(
        requirement="Key Managerial Personnel details must be disclosed",
        drhp_chapter="CHAPTER_V_ABOUT_COMPANY",
        user_document_chunks=[],
        regulation_type="Companies Act"
    )
    
    state1.status = "INSUFFICIENT"
    state1.explanation = "CEO name provided but missing DIN, CFO details, and Company Secretary"
    state1.evidence = "Our CEO is Mr. John Doe"
    state1.missing_details = "CEO DIN, CFO name and DIN, Company Secretary name and membership number"
    state1.confidence = 0.85
    state1.pages = [25, 26]
    
    state1.legal_requirements = [{
        'text': 'Section 203 requires disclosure of KMP with DIN/membership numbers',
        'section_number': '203',
        'chunk_id': 'COMPANIES_ACT_CH7_SEC203',
        'similarity_score': 0.92
    }]
    
    agent = SynthesisAgent()
    result1 = agent.execute(state1)
    
    # Test Case 2: MISSING status
    print("\n\n" + "="*80)
    print("TEST 2: MISSING Status")
    print("="*80)
    
    state2 = create_initial_state(
        requirement="Board meeting details must be disclosed",
        drhp_chapter="CHAPTER_V_ABOUT_COMPANY",
        user_document_chunks=[],
        regulation_type="Companies Act"
    )
    
    state2.status = "MISSING"
    state2.explanation = "No information found about board meetings"
    state2.evidence = ""
    state2.missing_details = "Number of board meetings, dates, director attendance, quorum details"
    state2.confidence = 0.9
    
    state2.legal_requirements = [{
        'text': 'Section 173 requires disclosure of board meeting details',
        'section_number': '173',
        'chunk_id': 'COMPANIES_ACT_CH7_SEC173'
    }]
    
    result2 = agent.execute(state2)
    
    print("\n✅ Synthesis Agent Tests Complete!")
