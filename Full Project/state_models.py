"""
State Management Models for Multi-Agent Compliance System
==========================================================
Pydantic models that define the state passed between agents

State Flow:
1. Initial State → Retrieval Agent
2. Retrieval Output → Analysis Agent  
3. Analysis Output → Validation Agent
4. Validation Output → Decision (Reanalysis or Synthesis)
5. Final Output → Synthesis Agent
"""

from typing import Dict, List, Optional, Literal, Any
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================================================
# CORE STATE MODEL
# ============================================================================

class ComplianceState(BaseModel):
    """
    Main state object passed between all agents
    Contains all information needed for compliance checking
    """
    
    # ===== INPUT DATA =====
    requirement: str = Field(description="Requirement being checked")
    drhp_chapter: str = Field(description="DRHP chapter name")
    regulation_type: str = Field(default="ICDR", description="ICDR or Companies Act")
    
    user_document_chunks: List[Dict[str, Any]] = Field(default_factory=list)

    # ===== RETRIEVAL AGENT OUTPUT =====
    user_relevant_chunks: List[Dict[str, Any]] = Field(default_factory=list)
    legal_requirements: List[Dict[str, Any]] = Field(default_factory=list)
    retrieval_metadata: Dict[str, Any] = Field(default_factory=dict)

    # ===== ANALYSIS AGENT OUTPUT =====
    status: Optional[Literal["PRESENT", "INSUFFICIENT", "MISSING", "UNCLEAR"]] = None
    explanation: Optional[str] = None
    evidence: Optional[str] = None
    missing_details: Optional[str] = None
    pages: List[int] = Field(default_factory=list)
    confidence: float = Field(default=0.0)

    # ===== VALIDATION AGENT OUTPUT =====
    validation_passed: bool = Field(default=False)
    validation_issues: List[str] = Field(default_factory=list)
    evidence_quality_score: float = Field(default=0.0)
    needs_reanalysis: bool = Field(default=False)

    # ===== REANALYSIS TRACKING =====
    reanalysis_count: int = Field(default=0)
    max_reanalysis_attempts: int = Field(default=2)
    reanalysis_history: List[Dict[str, Any]] = Field(default_factory=list)

    # ===== SYNTHESIS OUTPUT =====
    priority: Optional[Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]] = None
    legal_citation: Optional[str] = None
    recommendations: List[str] = Field(default_factory=list)

    # ===== OBLIGATION TRACEABILITY (CRITICAL) =====
    obligation_id: Optional[str] = Field(default=None)
    source_clause: Optional[str] = Field(default=None)
    mandatory: Optional[bool] = Field(default=None)

    # ===== METADATA =====
    processing_start_time: Optional[datetime] = None
    processing_end_time: Optional[datetime] = None
    agent_path: List[str] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True



# ============================================================================
# AGENT OUTPUT MODELS
# ============================================================================

class RetrievalOutput(BaseModel):
    """Output from Retrieval Agent"""
    user_chunks: List[Dict[str, Any]]
    legal_requirements: List[Dict[str, Any]]
    user_chunks_count: int
    legal_requirements_count: int
    retrieval_time_ms: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AnalysisOutput(BaseModel):
    """Output from Analysis Agent"""
    status: Literal["PRESENT", "INSUFFICIENT", "MISSING", "UNCLEAR"]
    explanation: str
    evidence: str
    missing_details: str
    confidence: float
    pages: List[int]
    analysis_time_ms: float


class ValidationOutput(BaseModel):
    """Output from Validation Agent"""
    validation_passed: bool
    validation_issues: List[str]
    evidence_quality_score: float
    needs_reanalysis: bool
    validation_criteria: Dict[str, bool]
    validation_time_ms: float


class ReanalysisOutput(BaseModel):
    """Output from Reanalysis Agent"""
    improved_status: Literal["PRESENT", "INSUFFICIENT", "MISSING", "UNCLEAR"]
    improved_explanation: str
    improved_evidence: str
    additional_context: List[Dict[str, Any]]
    reanalysis_reason: str
    reanalysis_time_ms: float


class SynthesisOutput(BaseModel):
    """Output from Synthesis Agent"""
    final_status: Literal["PRESENT", "INSUFFICIENT", "MISSING", "UNCLEAR"]
    final_explanation: str
    final_evidence: str
    final_missing_details: str
    priority: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    legal_citation: str
    recommendations: List[str]
    confidence: float
    total_processing_time_ms: float


# ============================================================================
# BATCH PROCESSING STATE
# ============================================================================

class BatchComplianceState(BaseModel):
    """State for processing multiple requirements"""
    
    requirements: List[str] = Field(description="List of requirements to check")
    drhp_chapter: str
    regulation_type: str
    
    # Document data (shared across all requirements)
    user_document_chunks: List[Dict[str, Any]]
    
    # Results for each requirement
    individual_results: List[ComplianceState] = Field(default_factory=list)
    
    # Batch summary
    total_requirements: int = Field(default=0)
    completed_requirements: int = Field(default=0)
    summary: Dict[str, int] = Field(default_factory=dict)
    priority_summary: Dict[str, int] = Field(default_factory=dict)
    
    # Timing
    batch_start_time: Optional[datetime] = None
    batch_end_time: Optional[datetime] = None


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_initial_state(
    requirement: str,
    drhp_chapter: str,
    user_document_chunks: List[Dict[str, Any]],
    regulation_type: str = "ICDR"
) -> ComplianceState:
    """
    Create initial state for a compliance check
    
    Args:
        requirement: The requirement to check
        drhp_chapter: DRHP chapter name
        user_document_chunks: Chunks from user's DRHP
        regulation_type: ICDR or Companies Act
    
    Returns:
        ComplianceState initialized for processing
    """
    return ComplianceState(
        requirement=requirement,
        drhp_chapter=drhp_chapter,
        user_document_chunks=user_document_chunks,
        regulation_type=regulation_type,
        processing_start_time=datetime.now(),
        agent_path=["INITIALIZED"]
    )


def state_to_dict(state: ComplianceState) -> Dict[str, Any]:
    """Convert state to dictionary for storage/API response"""
    return state.model_dump(
        exclude_none=True,
        exclude={
            'user_document_chunks',  # Exclude large data
            'user_relevant_chunks',
            'legal_requirements'
        }
    )


def update_agent_path(state: ComplianceState, agent_name: str) -> ComplianceState:
    """Update the agent path tracker"""
    state.agent_path.append(agent_name)
    return state


# ============================================================================
# VALIDATION HELPERS
# ============================================================================

def validate_state_for_agent(state: ComplianceState, agent_name: str) -> bool:
    """
    Validate that state has required fields for a specific agent
    
    Args:
        state: Current state
        agent_name: Which agent to validate for
    
    Returns:
        True if state is valid, False otherwise
    """
    
    if agent_name == "RETRIEVAL":
        return bool(state.requirement and state.user_document_chunks)
    
    elif agent_name == "ANALYSIS":
        return bool(
            state.requirement and
            (state.user_relevant_chunks or state.legal_requirements)
        )
    
    elif agent_name == "VALIDATION":
        return bool(
            state.status and
            state.explanation
        )
    
    elif agent_name == "REANALYSIS":
        return bool(
            state.status == "UNCLEAR" and
            state.reanalysis_count < state.max_reanalysis_attempts
        )
    
    elif agent_name == "SYNTHESIS":
        return bool(
            state.status and
            state.explanation
        )
    
    return False


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    """Test state models"""
    
    print("🧪 Testing State Models\n")
    
    # Create initial state
    state = create_initial_state(
        requirement="Risk factors must be disclosed prominently",
        drhp_chapter="CHAPTER_II_RISK_FACTORS",
        user_document_chunks=[
            {
                'text': 'Sample chunk 1',
                'page_number': 15
            },
            {
                'text': 'Sample chunk 2',
                'page_number': 16
            }
        ],
        regulation_type="ICDR"
    )
    
    print("✅ Initial State Created:")
    print(f"   Requirement: {state.requirement}")
    print(f"   Chapter: {state.drhp_chapter}")
    print(f"   Regulation: {state.regulation_type}")
    print(f"   Chunks: {len(state.user_document_chunks)}")
    
    # Simulate agent processing
    state = update_agent_path(state, "RETRIEVAL")
    state.user_relevant_chunks = [{'text': 'relevant', 'page': 15}]
    state.legal_requirements = [{'text': 'legal req', 'similarity': 0.85}]
    
    state = update_agent_path(state, "ANALYSIS")
    state.status = "INSUFFICIENT"
    state.explanation = "Risk factors mentioned but not prominent"
    state.confidence = 0.75
    
    state = update_agent_path(state, "VALIDATION")
    state.validation_passed = False
    state.needs_reanalysis = True
    
    print("\n✅ State After Processing:")
    print(f"   Agent Path: {' → '.join(state.agent_path)}")
    print(f"   Status: {state.status}")
    print(f"   Needs Reanalysis: {state.needs_reanalysis}")
    
    # Convert to dict
    result = state_to_dict(state)
    print(f"\n✅ Serialized: {len(result)} fields")
    
    print("\n🎉 State models working correctly!")
