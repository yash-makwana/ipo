from document_processor import process_pdf_with_docai, chunk_document
from google.cloud import storage
import json
import os

PROJECT_ID = os.environ.get('GCP_PROJECT')
UPLOAD_BUCKET = f"{PROJECT_ID}-uploads"
PROCESSED_BUCKET = f"{PROJECT_ID}-processed"

def process_uploaded_document(job_id):
    """
    Process an uploaded document:
    1. Run Document AI OCR
    2. Extract text with page numbers
    3. Create chunks
    4. Store results
    """
    
    storage_client = storage.Client()
    upload_bucket = storage_client.bucket(UPLOAD_BUCKET)
    processed_bucket = storage_client.bucket(PROCESSED_BUCKET)
    
    # Get job metadata
    metadata_blob = upload_bucket.blob(f"{job_id}/metadata.json")
    metadata = json.loads(metadata_blob.download_as_string())
    
    # Get GCS URI of uploaded file
    gcs_uri = f"gs://{UPLOAD_BUCKET}/{metadata['blob_path']}"
    
    print(f"Processing job {job_id}: {gcs_uri}")
    
    # Step 1: Process with Document AI
    doc_result = process_pdf_with_docai(gcs_uri)
    
    # Step 2: Create chunks
    chunks = chunk_document(doc_result['pages'])
    
    # Step 3: Store processed results
    processed_data = {
        'job_id': job_id,
        'total_pages': doc_result['total_pages'],
        'total_chunks': len(chunks),
        'pages': doc_result['pages'],
        'chunks': chunks,
        'metadata': metadata
    }
    
    # Save to processed bucket
    result_blob = processed_bucket.blob(f"{job_id}/processed.json")
    result_blob.upload_from_string(json.dumps(processed_data))
    
    # Update job status
    metadata['status'] = 'processed'
    metadata['processed_at'] = 'timestamp'
    metadata_blob.upload_from_string(json.dumps(metadata))
    
    print(f"✅ Job {job_id} processed successfully")
    return processed_data

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        job_id = sys.argv[1]
        process_uploaded_document(job_id)
