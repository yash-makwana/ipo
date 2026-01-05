"""
Flask API Integration for Multi-Agent Compliance System
=======================================================
Integrate the LangGraph multi-agent orchestrator with your Flask API

This file shows how to add multi-agent endpoints to your existing API.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from google.cloud import storage
import PyPDF2
from io import BytesIO

# Import the multi-agent orchestrator
from multi_agent_orchestrator import MultiAgentComplianceOrchestrator

# Import your existing DRHP mapping
# from drhp_mapping import get_regulations_for_drhp_section


app = Flask(__name__)
CORS(app)

# Initialize orchestrator (singleton)
orchestrator = None


def get_orchestrator():
    """Get or create orchestrator instance"""
    global orchestrator
    if orchestrator is None:
        orchestrator = MultiAgentComplianceOrchestrator()
    return orchestrator


def process_drhp_pdf(gcs_uri: str):
    """
    Process DRHP PDF from GCS into chunks
    
    Args:
        gcs_uri: GCS URI of the DRHP PDF
    
    Returns:
        Dict with chunks and metadata
    """
    try:
        storage_client = storage.Client()
        bucket_name = gcs_uri.split('/')[2]
        blob_path = '/'.join(gcs_uri.split('/')[3:])
        
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        pdf_bytes = blob.download_as_bytes()
        
        pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_bytes))
        chunks = []
        
        for page_num, page in enumerate(pdf_reader.pages):
            text = page.extract_text()
            
            if not text or len(text.strip()) < 50:
                continue
            
            # Create chunks (300 words each)
            words = text.split()
            for i in range(0, len(words), 300):
                chunk_text = ' '.join(words[i:i+300])
                if len(chunk_text.strip()) > 100:
                    chunks.append({
                        'chunk_id': len(chunks),
                        'text': chunk_text,
                        'page_number': page_num + 1
                    })
        
        return {
            'success': True,
            'chunks': chunks,
            'total_pages': len(pdf_reader.pages),
            'total_chunks': len(chunks)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


# ============================================================================
# NEW MULTI-AGENT ENDPOINTS
# ============================================================================

@app.route('/api/v2/compliance/check-requirement', methods=['POST'])
def check_single_requirement():
    """
    Check a single requirement using multi-agent system
    
    Request Body:
    {
        "gcs_uri": "gs://bucket/drhp.pdf",
        "requirement": "Risk factors must be disclosed",
        "drhp_chapter": "CHAPTER_II_RISK_FACTORS",
        "regulation_type": "ICDR"  // or "Companies Act"
    }
    
    Response:
    {
        "status": "INSUFFICIENT",
        "priority": "HIGH",
        "confidence": 0.85,
        "explanation": "...",
        "evidence": "...",
        "missing_details": "...",
        "pages": [15, 16],
        "legal_citation": "ICDR Regulation 6",
        "recommendations": [...],
        "agent_path": ["RETRIEVAL", "ANALYSIS", "VALIDATION", "SYNTHESIS"],
        "reanalysis_count": 0
    }
    """
    try:
        data = request.json
        
        # Validate request
        if not all(k in data for k in ['gcs_uri', 'requirement', 'drhp_chapter']):
            return jsonify({
                'error': 'Missing required fields: gcs_uri, requirement, drhp_chapter'
            }), 400
        
        # Process DRHP
        doc_result = process_drhp_pdf(data['gcs_uri'])
        if not doc_result['success']:
            return jsonify({
                'error': f"Failed to process DRHP: {doc_result.get('error')}"
            }), 400
        
        # Get orchestrator
        orch = get_orchestrator()
        
        # Execute multi-agent check
        result = orch.check_compliance(
            requirement=data['requirement'],
            user_document_chunks=doc_result['chunks'],
            drhp_chapter=data['drhp_chapter'],
            regulation_type=data.get('regulation_type', 'ICDR')
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'type': 'MultiAgentOrchestrationError'
        }), 500


@app.route('/api/v2/compliance/check-batch', methods=['POST'])
def check_batch_requirements():
    """
    Check multiple requirements using multi-agent system
    
    Request Body:
    {
        "gcs_uri": "gs://bucket/drhp.pdf",
        "requirements": [
            "Risk factors must be disclosed",
            "Board composition must be disclosed",
            ...
        ],
        "drhp_chapter": "CHAPTER_V_ABOUT_COMPANY",
        "regulation_type": "ICDR"
    }
    
    Response:
    {
        "total_requirements": 5,
        "processing_time_seconds": 45,
        "summary": {
            "PRESENT": 2,
            "INSUFFICIENT": 2,
            "MISSING": 1,
            "UNCLEAR": 0
        },
        "priority_summary": {
            "CRITICAL": 1,
            "HIGH": 2,
            "MEDIUM": 1,
            "LOW": 1
        },
        "items": [
            { ... individual results ... }
        ]
    }
    """
    try:
        data = request.json
        
        # Validate request
        if not all(k in data for k in ['gcs_uri', 'requirements', 'drhp_chapter']):
            return jsonify({
                'error': 'Missing required fields: gcs_uri, requirements, drhp_chapter'
            }), 400
        
        # Process DRHP
        doc_result = process_drhp_pdf(data['gcs_uri'])
        if not doc_result['success']:
            return jsonify({
                'error': f"Failed to process DRHP: {doc_result.get('error')}"
            }), 400
        
        # Get orchestrator
        orch = get_orchestrator()
        
        # Execute batch check
        result = orch.check_multiple_requirements(
            requirements=data['requirements'],
            user_document_chunks=doc_result['chunks'],
            drhp_chapter=data['drhp_chapter'],
            regulation_type=data.get('regulation_type', 'ICDR')
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'type': 'MultiAgentBatchError'
        }), 500


@app.route('/api/v2/compliance/check-chapter', methods=['POST'])
def check_full_chapter():
    """
    Check all requirements for a DRHP chapter using multi-agent system
    
    This uses your existing drhp_mapping to get all requirements for a chapter
    
    Request Body:
    {
        "gcs_uri": "gs://bucket/drhp.pdf",
        "chapter_key": "CHAPTER_II_RISK_FACTORS",
        "subchapter": "",  // optional
        "regulation_type": "ICDR"
    }
    
    Response: Same as check-batch
    """
    try:
        data = request.json
        
        # Validate request
        if not all(k in data for k in ['gcs_uri', 'chapter_key']):
            return jsonify({
                'error': 'Missing required fields: gcs_uri, chapter_key'
            }), 400
        
        # Get requirements from your existing mapping
        # Uncomment and use your actual mapping:
        # from drhp_mapping import get_regulations_for_drhp_section
        # mapping = get_regulations_for_drhp_section(
        #     data['chapter_key'],
        #     data.get('subchapter', '')
        # )
        # requirements = mapping.get('specific_checks', []) + mapping.get('subchapter_checks', [])
        
        # For now, return error to implement
        return jsonify({
            'error': 'TODO: Integrate with your drhp_mapping.py',
            'message': 'Uncomment the mapping code above'
        }), 501
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/api/v2/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        orch = get_orchestrator()
        return jsonify({
            'status': 'healthy',
            'orchestrator': 'initialized',
            'version': '2.0-multi-agent'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500


# ============================================================================
# BACKWARD COMPATIBILITY (Optional)
# ============================================================================

@app.route('/api/compliance/check', methods=['POST'])
def legacy_compliance_check():
    """
    Legacy endpoint - redirects to v2 multi-agent system
    
    This ensures backward compatibility with existing frontend
    """
    try:
        # Map legacy request to new format
        data = request.json
        
        # Call new endpoint
        return check_batch_requirements()
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    
    print("=" * 80)
    print("🚀 MULTI-AGENT COMPLIANCE API SERVER")
    print("=" * 80)
    print(f"Starting on port {port}")
    print("\nAvailable endpoints:")
    print("  POST /api/v2/compliance/check-requirement  - Single requirement")
    print("  POST /api/v2/compliance/check-batch        - Multiple requirements")
    print("  POST /api/v2/compliance/check-chapter      - Full chapter")
    print("  GET  /api/v2/health                        - Health check")
    print("=" * 80)
    
    app.run(host='0.0.0.0', port=port, debug=True)
