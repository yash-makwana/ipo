from google.cloud import documentai_v1 as documentai
from google.cloud import storage
import os
import json

PROJECT_ID = os.environ.get('GCP_PROJECT')
LOCATION = "us"
PROCESSOR_ID = os.environ.get('DOCAI_PROCESSOR_ID')

def process_pdf_with_docai(gcs_uri):
    """
    Process PDF using Document AI OCR
    
    Args:
        gcs_uri: GCS path like gs://bucket/file.pdf
    
    Returns:
        dict: Processed document with text and page mapping
    """
    
    # Initialize Document AI client
    client = documentai.DocumentProcessorServiceClient()
    
    # The full processor name
    name = f"projects/{PROJECT_ID}/locations/{LOCATION}/processors/{PROCESSOR_ID}"
    
    # Download file from GCS
    storage_client = storage.Client()
    bucket_name = gcs_uri.replace('gs://', '').split('/')[0]
    blob_path = '/'.join(gcs_uri.replace('gs://', '').split('/')[1:])
    
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_path)
    pdf_content = blob.download_as_bytes()
    
    # Configure the process request
    raw_document = documentai.RawDocument(
        content=pdf_content,
        mime_type="application/pdf"
    )
    
    request = documentai.ProcessRequest(
        name=name,
        raw_document=raw_document
    )
    
    # Process the document
    print(f"Processing document: {gcs_uri}")
    result = client.process_document(request=request)
    document = result.document
    
    # Extract text with page numbers
    pages_data = []
    
    for page_num, page in enumerate(document.pages, start=1):
        page_text = get_page_text(page, document.text)
        pages_data.append({
            'page_number': page_num,
            'text': page_text,
            'word_count': len(page_text.split())
        })
    
    return {
        'full_text': document.text,
        'pages': pages_data,
        'total_pages': len(document.pages)
    }

def get_page_text(page, full_text):
    """Extract text for a specific page"""
    page_text = ""
    
    for paragraph in page.paragraphs:
        for segment in paragraph.layout.text_anchor.text_segments:
            start_index = int(segment.start_index) if segment.start_index else 0
            end_index = int(segment.end_index) if segment.end_index else 0
            page_text += full_text[start_index:end_index]
        page_text += "\n"
    
    return page_text.strip()

def chunk_document(pages_data, chunk_size=1000, overlap=200):
    """
    Create overlapping chunks from pages while preserving page numbers
    
    Args:
        pages_data: List of page dictionaries
        chunk_size: Characters per chunk
        overlap: Overlap between chunks
    
    Returns:
        list: Chunks with metadata
    """
    chunks = []
    chunk_id = 0
    
    for page in pages_data:
        page_num = page['page_number']
        text = page['text']
        
        # Split page into chunks if it's long
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end]
            
            if chunk_text.strip():
                chunks.append({
                    'chunk_id': chunk_id,
                    'text': chunk_text,
                    'page_number': page_num,
                    'start_pos': start,
                    'end_pos': end
                })
                chunk_id += 1
            
            start = end - overlap  # Create overlap
    
    return chunks

if __name__ == "__main__":
    # Test the processor
    test_uri = "gs://your-bucket/test.pdf"
    result = process_pdf_with_docai(test_uri)
    print(f"Processed {result['total_pages']} pages")
    print(f"First page preview: {result['pages'][0]['text'][:200]}...")
