"""
Multi-Agent Compliance System - Agents Package
==============================================
Contains 5 specialized agents for IPO compliance checking

Agents:
1. RetrievalAgent - Searches DRHP + Neo4j for relevant content
2. AnalysisAgent - Compares user content vs legal requirements
3. ValidationAgent - Validates evidence quality and completeness
4. ReanalysisAgent - Iteratively refines UNCLEAR cases
5. SynthesisAgent - Generates final compliance report
"""

from .retrieval_agent import RetrievalAgent
from .analysis_agent import AnalysisAgent
from .validation_agent import ValidationAgent
from .reanalysis_agent import ReanalysisAgent
from .synthesis_agent import SynthesisAgent

__all__ = [
    'RetrievalAgent',
    'AnalysisAgent',
    'ValidationAgent',
    'ReanalysisAgent',
    'SynthesisAgent'
]

__version__ = '1.0.0'
