# main_local.py - LOCAL VERSION with NSE-Aligned Production Orchestrator
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from compliance_engine import get_compliance_engine
from drhp_mapping import get_regulations_for_drhp_section, get_all_drhp_chapters, get_neo4j_filters_for_chapter
from multi_agent_orchestrator import get_multi_agent_orchestrator
import uuid
import os
import json
from datetime import datetime, UTC
import traceback
import threading
import time
from dotenv import load_dotenv
from functools import wraps
from pathlib import Path

load_dotenv('.env-local')

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Local storage directories
UPLOAD_DIR = Path(os.environ.get('LOCAL_UPLOAD_DIR', './uploads'))
STORAGE_DIR = Path(os.environ.get('LOCAL_STORAGE_DIR', './storage'))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# Initialize services
try:
    multi_agent_orchestrator = get_multi_agent_orchestrator("ICDR")
    print("✅ Multi-Agent Orchestrator ENABLED (NSE-Aligned Production)")
except Exception as e:
    print(f"⚠️  Could not initialize multi-agent: {e}")
    multi_agent_orchestrator = None

AUTH_ENABLED = os.environ.get('AUTH_ENABLED', 'false').lower() == 'true'

# ✅ PRODUCTION CONFIGURATION (Updated)
INITIAL_OBLIGATION_LIMIT = int(os.environ.get('INITIAL_OBLIGATION_LIMIT', '30'))
RUN_INTERNAL_CHECKS = os.environ.get('RUN_INTERNAL_CHECKS', 'true').lower() == 'true'

print(f"🔧 Configuration:")
print(f"   Storage: {STORAGE_DIR}")
print(f"   Uploads: {UPLOAD_DIR}")
print(f"   Auth: {'✅ Enabled' if AUTH_ENABLED else '⚠️  Disabled (Local Mode)'}")
print(f"   Multi-Agent: {'✅ Enabled (NSE-Aligned)' if multi_agent_orchestrator else '❌ Disabled'}")
print(f"   Initial Limit: {INITIAL_OBLIGATION_LIMIT}")
print(f"   Internal Checks: {'✅ Enabled' if RUN_INTERNAL_CHECKS else '⚠️  Disabled'}")

# ============================================================================
# STORAGE HELPERS
# ============================================================================

def get_job(job_id):
    """Get job from local storage"""
    try:
        job_file = STORAGE_DIR / f"{job_id}.json"
        if not job_file.exists():
            return None
        with open(job_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️  Error getting job {job_id}: {e}")
        return None

def save_job(job_id, job_data):
    """Save job to local storage"""
    try:
        # Ensure created_at exists and is an ISO string
        if job_data.get('created_at') is None:
            try:
                job_data['created_at'] = datetime.now(UTC).isoformat()
            except Exception:
                job_data['created_at'] = str(datetime.now())

        job_file = STORAGE_DIR / f"{job_id}.json"
        with open(job_file, 'w') as f:
            json.dump(job_data, f, default=str, indent=2)
    except Exception as e:
        print(f"⚠️  Could not save job: {e}")

def get_user_history(user_email=None, limit=50):
    """Get user history from local storage"""
    try:
        reports = []
        for job_file in STORAGE_DIR.glob("*.json"):
            try:
                with open(job_file, 'r') as f:
                    job_data = json.load(f)
                    if user_email is None or job_data.get('user_email') == user_email:
                        # Normalize created_at for safe sorting (handle None or datetime objects)
                        created_at = job_data.get('created_at')
                        job_data['_created_at_str'] = str(created_at) if created_at is not None else ''
                        reports.append(job_data)
            except Exception as e:
                print(f"⚠️  Skipping malformed job file {job_file}: {e}")
                continue

        reports.sort(key=lambda x: x.get('_created_at_str', ''), reverse=True)
        # Remove internal helper key before returning
        for r in reports:
            if '_created_at_str' in r:
                r.pop('_created_at_str')

        return reports[:limit]
    except Exception as e:
        print(f"⚠️  Error getting history: {e}")
        return []

# ============================================================================
# AUTH HELPERS
# ============================================================================

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not AUTH_ENABLED:
            request.user_email = 'local_user@localhost'
            request.user_name = 'Local User'
            return f(*args, **kwargs)
        
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'No authorization'}), 401
        
        request.user_email = 'authenticated_user@localhost'
        request.user_name = 'Authenticated User'
        return f(*args, **kwargs)
    
    return decorated_function

# ============================================================================
# ROUTES
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'service': 'IPO Compliance API (NSE-Aligned)',
        'version': '9.0-production-nse',
        'auth_enabled': AUTH_ENABLED,
        'mode': 'NSE_ALIGNED_PRODUCTION' if multi_agent_orchestrator else 'STANDARD',
        'storage': 'LOCAL_FILESYSTEM',
        'initial_limit': INITIAL_OBLIGATION_LIMIT,
        'features': {
            'system_a_silent': True,
            'system_b_nse_queries': True,
            'ipo_applicability_filtering': True,
            'cross_page_inconsistency': True,
            'table_detection': True,
            'dynamic_severity': True
        }
    })

@app.route('/api/user/history', methods=['GET'])
@require_auth
def get_history():
    """Get user history"""
    try:
        user_email = request.user_email
        limit = request.args.get('limit', 50, type=int)
        
        reports = get_user_history(user_email, limit)
        
        return jsonify({'reports': reports, 'count': len(reports)}), 200
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'reports': [], 'count': 0}), 200

@app.route('/api/drhp/chapters', methods=['GET'])
def get_drhp_chapters():
    """Get DRHP chapters"""
    try:
        chapters = get_all_drhp_chapters()
        return jsonify({'chapters': chapters, 'count': len(chapters)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/compliance/check-by-drhp', methods=['POST'])
@require_auth
def check_compliance_by_drhp():
    """Check compliance with NSE-aligned production orchestrator"""
    try:
        user_email = request.user_email
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if not file or file.filename == '':
            return jsonify({'error': 'Empty file'}), 400
        
        drhp_chapter = request.form.get('drhp_chapter', '').strip()
        regulation_type = request.form.get('regulation_type', 'ICDR').strip()
        
        if not drhp_chapter:
            return jsonify({'error': 'Chapter not specified'}), 400
        
        mapping = get_regulations_for_drhp_section(drhp_chapter)
        
        if not mapping:
            return jsonify({'error': f'Unknown chapter: {drhp_chapter}'}), 400
        
        # Save file
        job_id = str(uuid.uuid4())
        job_dir = UPLOAD_DIR / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        
        local_file_path = job_dir / file.filename
        file.save(local_file_path)
        
        # Get Neo4j filters
        neo4j_filters = get_neo4j_filters_for_chapter(drhp_chapter, regulation_type)
        
        # Create job
        job_data = {
            'status': 'queued',
            'job_id': job_id,
            'user_email': user_email,
            'drhp_chapter': drhp_chapter,
            'drhp_chapter_name': mapping['drhp_chapter_name'],
            'regulation_type': regulation_type,
            'use_multi_agent': multi_agent_orchestrator is not None,
            'initial_limit': INITIAL_OBLIGATION_LIMIT,
            'document_name': file.filename,
            'local_file_path': str(local_file_path),
            'created_at': datetime.now(UTC).isoformat(),
            'progress': 'Queued for NSE-aligned compliance check...',
            'mode': 'NSE_ALIGNED_PRODUCTION' if multi_agent_orchestrator else 'STANDARD',
            'neo4j_chapters': neo4j_filters['chapters'],
            'mandatory_only': neo4j_filters.get('mandatory_only', False)
        }
        
        save_job(job_id, job_data)
        
        # Process in background
        thread = threading.Thread(
            target=process_compliance_check,
            args=(job_id, str(local_file_path), mapping, file.filename, regulation_type, neo4j_filters)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'job_id': job_id,
            'status': 'queued',
            'drhp_chapter': mapping['drhp_chapter_name'],
            'mode': job_data['mode'],
            'estimated_time_seconds': 90
        }), 202
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

def process_compliance_check(job_id, file_path, mapping, document_name, regulation_type='ICDR', neo4j_filters=None):
    """Background processing with NSE-aligned production orchestrator"""
    start_time = time.time()
    
    try:
        job_data = get_job(job_id)
        if not job_data:
            return
            
        job_data['status'] = 'processing'
        job_data['started_at'] = datetime.now(UTC).isoformat()
        job_data['progress'] = 'NSE-aligned compliance check starting...'
        save_job(job_id, job_data)
        
        if multi_agent_orchestrator:
            chapter_filters = neo4j_filters.get('chapters', [])
            mandatory_only = neo4j_filters.get('mandatory_only', False)
            drhp_chapter = job_data['drhp_chapter_name']
            
            if not chapter_filters:
                raise Exception("No Neo4j chapter filters specified")
            
            job_data['progress'] = f'Processing with NSE-aligned orchestrator (IPO applicability filtering enabled)...'
            save_job(job_id, job_data)
            
            print(f"\n{'='*80}")
            print(f"🚀 Starting NSE-Aligned Compliance Check")
            print(f"{'='*80}")
            print(f"Job ID: {job_id}")
            print(f"DRHP File: {file_path}")
            print(f"Chapter: {drhp_chapter}")
            print(f"Filters: {chapter_filters}")
            print(f"{'='*80}\n")
            
            # ✅ UPDATED: Use production orchestrator with correct parameters
            result = multi_agent_orchestrator.check_drhp_compliance(
                drhp_file_path=file_path,
                drhp_chapter=drhp_chapter,
                chapter_filters=chapter_filters,
                mandatory_only=mandatory_only,
                initial_limit=INITIAL_OBLIGATION_LIMIT,
                run_internal_checks=RUN_INTERNAL_CHECKS,
                output_format="structured"
            )
            
            # ✅ NEW: Extract results from production orchestrator output
            company_name = result.get('company_name', 'the Company')
            nse_queries = result.get('nse_queries', [])
            total_queries = result.get('total_queries', len(nse_queries))
            ipo_structure = result.get('ipo_structure', {})
            internal_stats = result.get('internal_stats', {})
            company_profile = result.get('company_profile', {})
            
            print(f"\n✅ Compliance Check Completed")
            print(f"   Company: {company_name}")
            print(f"   Total NSE Queries: {total_queries}")
            print(f"   Internal Checks: {internal_stats.get('total_checked', 0)} checked, "
                  f"{internal_stats.get('total_skipped', 0)} skipped")
            print(f"   Processing Time: {result.get('processing_time_seconds', 0)}s\n")
        
        else:
            # Fallback to standard engine
            engine = get_compliance_engine(regulation_type)
            result = engine.check_drhp_compliance(file_path, mapping)
            
            # Extract for compatibility
            company_name = 'the Company'
            nse_queries = []
            total_queries = 0
            ipo_structure = {}
            internal_stats = {}
            company_profile = {}
        
        elapsed_time = time.time() - start_time
        
        # ✅ UPDATED: New response format aligned with production orchestrator
        final_job = {
            'status': 'completed',
            'job_id': job_id,
            'user_email': job_data.get('user_email'),
            'mode': 'NSE_ALIGNED_PRODUCTION' if multi_agent_orchestrator else 'STANDARD',
            'regulation_type': regulation_type,
            'drhp_chapter': job_data['drhp_chapter'],
            'drhp_chapter_name': mapping.get('drhp_chapter_name', ''),
            'document_name': document_name,
            
            # ✅ NEW: NSE-aligned output
            'company_name': company_name,
            'company_profile': company_profile,
            'ipo_structure': ipo_structure,
            'nse_queries': nse_queries,
            'nse_engine_gemini_enabled': result.get('nse_engine_gemini_enabled', False),
            'total_queries': total_queries,
            
            # ✅ Internal stats (for logging/debugging only)
            'internal_stats': internal_stats,
            
            # Legacy compatibility (if needed by frontend)
            'total_requirements': total_queries,
            'summary': {
                'total': total_queries,
                'Major': sum(1 for q in nse_queries if q.get('severity') == 'Major'),
                'Observation': sum(1 for q in nse_queries if q.get('severity') == 'Observation'),
                'Clarification': sum(1 for q in nse_queries if q.get('severity') == 'Clarification')
            },
            
            # Metadata
            'completed_at': datetime.now(UTC).isoformat(),
            'processing_time_seconds': int(elapsed_time),
            'created_at': job_data.get('created_at')
        }
        
        save_job(job_id, final_job)
        
    except Exception as e:
        print(f"❌ Processing Error: {str(e)}")
        traceback.print_exc()
        
        job_data = get_job(job_id) or {'job_id': job_id}
        job_data['status'] = 'failed'
        job_data['error'] = str(e)
        job_data['error_traceback'] = traceback.format_exc()
        job_data['completed_at'] = datetime.now(UTC).isoformat()
        save_job(job_id, job_data)

@app.route('/api/compliance/status/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get job status"""
    try:
        job_data = get_job(job_id)
        if not job_data:
            return jsonify({'error': 'Job not found'}), 404
        
        # Return status info
        return jsonify({
            'job_id': job_id,
            'status': job_data.get('status', 'unknown'),
            'progress': job_data.get('progress', ''),
            'created_at': job_data.get('created_at'),
            'started_at': job_data.get('started_at'),
            'completed_at': job_data.get('completed_at'),
            'processing_time_seconds': job_data.get('processing_time_seconds'),
            'error': job_data.get('error')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/compliance/report/<job_id>', methods=['GET'])
def get_compliance_report(job_id):
    """Get full compliance report"""
    try:
        job_data = get_job(job_id)
        if not job_data:
            return jsonify({'error': 'Job not found'}), 404
        
        return jsonify(job_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/compliance/export/<job_id>', methods=['GET'])
def export_compliance_report(job_id):
    """Export compliance report as JSON file"""
    try:
        job_data = get_job(job_id)
        if not job_data:
            return jsonify({'error': 'Job not found'}), 404
        
        # Create export file
        export_file = STORAGE_DIR / f"{job_id}_export.json"
        with open(export_file, 'w') as f:
            json.dump(job_data, f, indent=2, default=str)
        
        return send_file(
            export_file,
            as_attachment=True,
            download_name=f"compliance_report_{job_id}.json",
            mimetype='application/json'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"\n{'='*80}")
    print(f"🚀 STARTING IPO COMPLIANCE API (NSE-Aligned Production)")
    print(f"{'='*80}")
    print(f"   Port: {port}")
    print(f"   Auth: {'✅ Enabled' if AUTH_ENABLED else '⚠️  Disabled'}")
    print(f"   Storage: {STORAGE_DIR}")
    print(f"   Mode: {'🎯 NSE-Aligned Production' if multi_agent_orchestrator else '🔧 Standard'}")
    print(f"   Initial Limit: {INITIAL_OBLIGATION_LIMIT} obligations")
    print(f"   Internal Checks: {'✅ Enabled (Silent)' if RUN_INTERNAL_CHECKS else '⚠️  Disabled'}")
    print(f"\n   Features:")
    print(f"   ✅ IPO Applicability Filtering")
    print(f"   ✅ System A (Silent Internal Validation)")
    print(f"   ✅ System B (NSE Content Queries)")
    print(f"   ✅ Cross-Page Inconsistency Detection")
    print(f"   ✅ Table Detection & Enforcement")
    print(f"   ✅ Dynamic Severity Escalation")
    print(f"{'='*80}\n")
    
    app.run(host='0.0.0.0', port=port, debug=True)