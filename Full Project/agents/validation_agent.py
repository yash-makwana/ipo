"""
Validation Agent
===============
Responsible for validating the analysis output

Checks:
1. Evidence quality - Is the evidence strong enough?
2. Confidence levels - Is the LLM confident in its analysis?
3. Completeness - Are all required fields populated?
4. Consistency - Does the status match the explanation?

Determines: Should this case be sent to Re-analysis Agent?
"""

import time
from typing import Dict, Any, List, Tuple
import sys
import os
import traceback

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from state_models import ComplianceState, ValidationOutput, update_agent_path


class ValidationAgent:
    """
    Validation Agent - Quality Control with comprehensive error handling
    
    Responsibilities:
    1. Validate analysis output quality
    2. Check evidence strength
    3. Identify cases needing reanalysis
    4. Flag inconsistencies
    """
    
    def __init__(self):
        """Initialize Validation Agent"""
        print(f"✅ ValidationAgent initialized")
    
    def validate_evidence_quality(self, state: ComplianceState) -> Tuple[float, List[str]]:
        """
        Validate the quality of evidence
        
        Args:
            state: Current state with analysis results
        
        Returns:
            (quality_score, list of issues)
        """
        issues = []
        score = 1.0
        
        try:
            # Check 1: Evidence exists for PRESENT/INSUFFICIENT status
            if state.status in ['PRESENT', 'INSUFFICIENT']:
                if not state.evidence or len(str(state.evidence).strip()) < 20:
                    issues.append("Status is PRESENT/INSUFFICIENT but evidence is missing or too short")
                    score -= 0.3
            
            # Check 2: Missing details specified for INSUFFICIENT/MISSING
            if state.status in ['INSUFFICIENT', 'MISSING']:
                missing = str(state.missing_details).lower()
                if not state.missing_details or len(missing.strip()) < 20:
                    issues.append("Status is INSUFFICIENT/MISSING but missing_details not specified")
                    score -= 0.3
                elif "more details" in missing or "more information" in missing:
                    issues.append("Missing details are too generic")
                    score -= 0.2
            
            # Check 3: Evidence length appropriate
            if state.evidence and len(str(state.evidence)) > 500:
                issues.append("Evidence is too long (>500 chars)")
                score -= 0.1
            
            # Check 4: Pages referenced for user content
            if state.user_relevant_chunks and not state.pages:
                issues.append("User content found but no pages referenced")
                score -= 0.2
        
        except Exception as e:
            print(f"⚠️  Error in evidence validation: {e}")
            traceback.print_exc()
            issues.append(f"Validation error: {str(e)}")
            score = 0.5
        
        return max(0.0, score), issues
    
    def validate_confidence_consistency(self, state: ComplianceState) -> Tuple[bool, List[str]]:
        """
        Check if confidence level matches the status and evidence
        
        Args:
            state: Current state
        
        Returns:
            (is_consistent, list of issues)
        """
        issues = []
        is_consistent = True
        
        try:
            confidence = float(state.confidence) if state.confidence is not None else 0.5
            
            # Check 1: UNCLEAR status should have low confidence
            if state.status == "UNCLEAR" and confidence > 0.6:
                issues.append(f"Status is UNCLEAR but confidence is high ({confidence:.2f})")
                is_consistent = False
            
            # Check 2: PRESENT status should have high confidence
            if state.status == "PRESENT" and confidence < 0.7:
                issues.append(f"Status is PRESENT but confidence is low ({confidence:.2f})")
                is_consistent = False
            
            # Check 3: Very low confidence should be UNCLEAR
            if confidence < 0.5 and state.status != "UNCLEAR":
                issues.append(f"Confidence is very low ({confidence:.2f}) but status is {state.status}")
                is_consistent = False
        
        except Exception as e:
            print(f"⚠️  Error in confidence validation: {e}")
            traceback.print_exc()
            issues.append(f"Validation error: {str(e)}")
            is_consistent = False
        
        return is_consistent, issues
    
    def check_needs_reanalysis(self, state: ComplianceState) -> Tuple[bool, str]:
        """
        Determine if this case needs reanalysis
        
        Args:
            state: Current state
        
        Returns:
            (needs_reanalysis, reason)
        """
        try:
            # Don't reanalyze if already done max attempts
            if state.reanalysis_count >= state.max_reanalysis_attempts:
                return False, "Max reanalysis attempts reached"
            
            # Reanalyze if status is UNCLEAR
            if state.status == "UNCLEAR":
                return True, "Status is UNCLEAR - needs more context"
            
            # Reanalyze if confidence is very low
            confidence = float(state.confidence) if state.confidence is not None else 0.5
            if confidence < 0.5:
                return True, f"Confidence too low ({confidence:.2f})"
            
            # Reanalyze if evidence quality is poor
            if state.status in ['PRESENT', 'INSUFFICIENT']:
                if not state.evidence or len(str(state.evidence).strip()) < 20:
                    return True, "Evidence quality insufficient"
            
            # Reanalyze if no legal requirements found
            if not state.legal_requirements and state.status != "MISSING":
                return True, "No legal requirements found"
            
            return False, "Validation passed"
        
        except Exception as e:
            print(f"⚠️  Error checking reanalysis: {e}")
            traceback.print_exc()
            return False, f"Error: {str(e)}"
    
    def validate_completeness(self, state: ComplianceState) -> Tuple[bool, List[str]]:
        """
        Check if all required fields are populated
        
        Args:
            state: Current state
        
        Returns:
            (is_complete, list of missing fields)
        """
        missing_fields = []
        
        try:
            if not state.status:
                missing_fields.append("status")
            
            if not state.explanation:
                missing_fields.append("explanation")
            
            if state.confidence is None or state.confidence == 0.0:
                missing_fields.append("confidence")
        
        except Exception as e:
            print(f"⚠️  Error in completeness check: {e}")
            traceback.print_exc()
            missing_fields.append(f"error: {str(e)}")
        
        is_complete = len(missing_fields) == 0
        return is_complete, missing_fields
    
    def execute(self, state: ComplianceState) -> ComplianceState:
        """
        Execute validation agent with comprehensive error handling
        
        Args:
            state: Current state with analysis results
        
        Returns:
            Updated state with validation results
        """
        print(f"\n{'='*60}")
        print(f"✅ VALIDATION AGENT")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            # Update agent path
            state = update_agent_path(state, "VALIDATION")
            
            # Validate completeness
            is_complete, missing_fields = self.validate_completeness(state)
            if not is_complete:
                print(f"   ⚠️  Missing fields: {missing_fields}")
            
            # Validate evidence quality
            evidence_score, evidence_issues = self.validate_evidence_quality(state)
            state.evidence_quality_score = evidence_score
            
            if evidence_issues:
                print(f"   ⚠️  Evidence issues ({len(evidence_issues)}):")
                for issue in evidence_issues:
                    print(f"      - {issue}")
            
            # Validate confidence consistency
            is_consistent, consistency_issues = self.validate_confidence_consistency(state)
            
            if consistency_issues:
                print(f"   ⚠️  Consistency issues ({len(consistency_issues)}):")
                for issue in consistency_issues:
                    print(f"      - {issue}")
            
            # Determine if reanalysis needed
            needs_reanalysis, reanalysis_reason = self.check_needs_reanalysis(state)
            state.needs_reanalysis = needs_reanalysis
            
            # Aggregate validation results
            all_issues = [f"Missing: {f}" for f in missing_fields] + evidence_issues + consistency_issues
            state.validation_issues = all_issues
            state.validation_passed = (
                is_complete and
                evidence_score >= 0.6 and
                is_consistent and
                not needs_reanalysis
            )
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            # Print results
            print(f"\n{'─'*60}")
            print(f"Validation Results:")
            print(f"{'─'*60}")
            print(f"   Complete: {'✅' if is_complete else '❌'}")
            print(f"   Evidence Quality: {evidence_score:.2f}")
            print(f"   Consistent: {'✅' if is_consistent else '⚠️ '}")
            print(f"   Needs Reanalysis: {'🔄 YES' if needs_reanalysis else '✅ NO'}")
            if needs_reanalysis:
                print(f"   Reason: {reanalysis_reason}")
            print(f"   Validation Passed: {'✅' if state.validation_passed else '❌'}")
            print(f"   Time: {elapsed_ms:.0f}ms")
        
        except Exception as e:
            print(f"\n❌ Validation error: {e}")
            traceback.print_exc()
            
            # Set safe defaults on error
            state.validation_passed = False
            state.needs_reanalysis = False
            state.validation_issues = [f"Validation error: {str(e)}"]
            state.evidence_quality_score = 0.5
        
        return state


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """Test Validation Agent"""
    
    print("=" * 80)
    print("🧪 TESTING VALIDATION AGENT")
    print("=" * 80)
    
    from state_models import create_initial_state
    
    # Test Case 1: Good analysis
    print("\n" + "="*80)
    print("TEST 1: Good Analysis (Should Pass)")
    print("="*80)
    
    state1 = create_initial_state(
        requirement="Test requirement",
        drhp_chapter="TEST",
        user_document_chunks=[],
        regulation_type="ICDR"
    )
    state1.status = "INSUFFICIENT"
    state1.explanation = "User provides CEO name but missing DIN"
    state1.evidence = "CEO is Mr. John Doe"
    state1.missing_details = "CEO DIN, CFO details"
    state1.confidence = 0.85
    state1.pages = [15]
    state1.user_relevant_chunks = [{'text': 'test', 'page_number': 15}]
    
    agent = ValidationAgent()
    result1 = agent.execute(state1)
    
    print(f"\nResult: {'PASSED ✅' if result1.validation_passed else 'FAILED ❌'}")
    
    print("\n✅ Validation Agent Test Complete!")