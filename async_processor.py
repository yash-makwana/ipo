# async_processor.py
# Background processing for compliance checks

from compliance_engine_vertax import get_compliance_engine
from google.cloud import storage
import json
import os
import threading

PROJECT_ID = os.environ.get('GCP_PROJECT')
UPLOAD_BUCKET = f"{PROJECT_ID}-uploads"

def process_compliance_async(job_id, regulation, chapter_id, subchapter_id, gcs_uri):
    """
    Process compliance check in background thread
    """
    storage_client = storage.Client()
    bucket = storage_client.bucket(UPLOAD_BUCKET)
    
    try:
        print(f"🚀 Background processing started for job {job_id}")
        
        # Update status to processing
        metadata_blob = bucket.blob(f"{job_id}/metadata.json")
        metadata = json.loads(metadata_blob.download_as_string())
        metadata['status'] = 'processing'
        metadata['progress'] = 'Initializing compliance engine...'
        metadata_blob.upload_from_string(json.dumps(metadata))
        
        # Get compliance engine
        engine = get_compliance_engine()
        
        # Update progress
        metadata['progress'] = 'Processing document and checking compliance...'
        metadata_blob.upload_from_string(json.dumps(metadata))
        
        # Run compliance check
        report = engine.check_compliance(
            regulation=regulation,
            chapter_id=chapter_id,
            subchapter_id=subchapter_id if subchapter_id else None,
            gcs_uri=gcs_uri
        )
        
        print(f"✅ Compliance check completed for job {job_id}: {len(report.get('items', []))} items")
        
        # Store report
        report_blob = bucket.blob(f"{job_id}/report.json")
        report_blob.upload_from_string(json.dumps(report))
        
        # Update metadata to completed
        metadata['status'] = 'completed'
        metadata['progress'] = 'Compliance check complete'
        metadata_blob.upload_from_string(json.dumps(metadata))
        
    except Exception as e:
        print(f"❌ Error processing job {job_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Update metadata to failed
        try:
            metadata = json.loads(metadata_blob.download_as_string())
            metadata['status'] = 'failed'
            metadata['error'] = str(e)
            metadata['progress'] = f'Failed: {str(e)}'
            metadata_blob.upload_from_string(json.dumps(metadata))
        except:
            pass

def start_background_processing(job_id, regulation, chapter_id, subchapter_id, gcs_uri):
    """
    Start processing in a background thread
    """
    thread = threading.Thread(
        target=process_compliance_async,
        args=(job_id, regulation, chapter_id, subchapter_id, gcs_uri)
    )
    thread.daemon = True
    thread.start()
    print(f"✅ Background thread started for job {job_id}")
