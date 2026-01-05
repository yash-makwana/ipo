#!/bin/bash
# diagnose.sh - Diagnostic tool for IPO Compliance System

set -e

echo "========================================"
echo "🔍 IPO Compliance System Diagnostics"
echo "========================================"
echo ""

PROJECT_ID="iposakhi"
REGION="us-central1"
SERVICE_NAME="compliance-api"
BUCKET_NAME="${PROJECT_ID}-uploads"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

info() {
    echo "ℹ️  $1"
}

# Check 1: gcloud authentication
echo "1️⃣  Checking gcloud authentication..."
if gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)")
    success "Authenticated as: $ACCOUNT"
else
    error "Not authenticated"
    info "Run: gcloud auth login"
    exit 1
fi
echo ""

# Check 2: Service exists
echo "2️⃣  Checking Cloud Run service..."
if gcloud run services describe $SERVICE_NAME --region=$REGION --project=$PROJECT_ID &>/dev/null; then
    success "Service $SERVICE_NAME exists"
    
    # Get service URL
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
        --region=$REGION \
        --project=$PROJECT_ID \
        --format='value(status.url)')
    info "Service URL: $SERVICE_URL"
else
    error "Service $SERVICE_NAME not found"
    exit 1
fi
echo ""

# Check 3: Environment variables
echo "3️⃣  Checking environment variables..."
ENV_VARS=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --format='value(spec.template.spec.containers[0].env)')

if echo "$ENV_VARS" | grep -q "GCS_BUCKET"; then
    success "GCS_BUCKET is set"
    BUCKET_VALUE=$(echo "$ENV_VARS" | grep GCS_BUCKET | cut -d'=' -f2)
    info "   Value: $BUCKET_VALUE"
else
    error "GCS_BUCKET not set!"
    warning "This is likely causing your issue"
    info "Fix: gcloud run services update $SERVICE_NAME --region=$REGION --set-env-vars='GCS_BUCKET=$BUCKET_NAME'"
fi

if echo "$ENV_VARS" | grep -q "GCP_PROJECT"; then
    success "GCP_PROJECT is set"
else
    warning "GCP_PROJECT not explicitly set"
fi
echo ""

# Check 4: Service configuration
echo "4️⃣  Checking service configuration..."
MEMORY=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --format='value(spec.template.spec.containers[0].resources.limits.memory)')
info "Memory: $MEMORY"

TIMEOUT=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --format='value(spec.template.spec.containers[0].resources.limits.cpu)')
info "CPU: $TIMEOUT"

REQ_TIMEOUT=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --format='value(spec.template.spec.timeoutSeconds)')
info "Request Timeout: ${REQ_TIMEOUT}s"

if [ "$REQ_TIMEOUT" -lt 600 ]; then
    warning "Timeout is less than 10 minutes (600s)"
    info "Recommended: 600s or more for large documents"
fi
echo ""

# Check 5: GCS Bucket
echo "5️⃣  Checking GCS bucket..."
if gsutil ls gs://${BUCKET_NAME}/ &>/dev/null; then
    success "Bucket gs://${BUCKET_NAME}/ exists"
    
    # Check recent uploads
    UPLOAD_COUNT=$(gsutil ls -r gs://${BUCKET_NAME}/uploads/ 2>/dev/null | grep -c ".pdf$" || echo "0")
    info "Recent PDF uploads: $UPLOAD_COUNT"
else
    error "Bucket gs://${BUCKET_NAME}/ not found!"
    info "Create it: gsutil mb -p $PROJECT_ID -l $REGION gs://${BUCKET_NAME}/"
fi
echo ""

# Check 6: Health endpoint
echo "6️⃣  Testing health endpoint..."
HTTP_CODE=$(curl -s -o /tmp/health_check.json -w "%{http_code}" "$SERVICE_URL/api/health")

if [ "$HTTP_CODE" = "200" ]; then
    success "Health check passed (HTTP $HTTP_CODE)"
    
    # Parse response
    if command -v python3 &> /dev/null; then
        VERSION=$(cat /tmp/health_check.json | python3 -c "import sys, json; print(json.load(sys.stdin).get('version', 'unknown'))")
        BUCKET_CONFIG=$(cat /tmp/health_check.json | python3 -c "import sys, json; print(json.load(sys.stdin).get('bucket', 'not set'))")
        
        info "Version: $VERSION"
        info "Configured bucket: $BUCKET_CONFIG"
        
        if [[ "$VERSION" == *"fixed"* ]] || [[ "$VERSION" == *"optimized"* ]]; then
            success "Using fixed version!"
        else
            warning "Not using fixed version"
            info "Deploy the fixed version to resolve issues"
        fi
        
        if [ "$BUCKET_CONFIG" = "$BUCKET_NAME" ]; then
            success "Bucket configuration matches!"
        else
            error "Bucket mismatch! Expected: $BUCKET_NAME, Got: $BUCKET_CONFIG"
        fi
    fi
else
    error "Health check failed (HTTP $HTTP_CODE)"
    cat /tmp/health_check.json
fi
echo ""

# Check 7: Recent logs
echo "7️⃣  Checking recent logs for errors..."
RECENT_ERRORS=$(gcloud run services logs read $SERVICE_NAME \
    --region=$REGION \
    --limit=50 \
    --format='value(textPayload)' | grep -i "error\|failed\|timeout" | wc -l)

if [ "$RECENT_ERRORS" -gt 0 ]; then
    warning "Found $RECENT_ERRORS error messages in recent logs"
    info "View logs: gcloud run services logs read $SERVICE_NAME --region=$REGION --limit=100"
else
    success "No recent errors in logs"
fi
echo ""

# Check 8: Active jobs
echo "8️⃣  Checking for stuck jobs..."
JOBS=$(gsutil ls gs://${BUCKET_NAME}/*/metadata.json 2>/dev/null | wc -l || echo "0")
info "Total jobs in bucket: $JOBS"

if [ "$JOBS" -gt 0 ]; then
    # Check for stuck jobs
    STUCK_COUNT=0
    for metadata_file in $(gsutil ls gs://${BUCKET_NAME}/*/metadata.json 2>/dev/null | head -5); do
        METADATA=$(gsutil cat "$metadata_file" 2>/dev/null)
        STATUS=$(echo "$METADATA" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'unknown'))" 2>/dev/null)
        
        if [ "$STATUS" = "processing" ] || [ "$STATUS" = "queued" ]; then
            STUCK_COUNT=$((STUCK_COUNT + 1))
            JOB_ID=$(echo "$metadata_file" | grep -oP '(?<=uploads/)[^/]+')
            warning "Possibly stuck job: $JOB_ID (status: $STATUS)"
        fi
    done
    
    if [ "$STUCK_COUNT" -gt 0 ]; then
        warning "Found $STUCK_COUNT potentially stuck jobs"
        info "These may be from before the fix was applied"
    else
        success "No stuck jobs found"
    fi
else
    info "No jobs in bucket yet"
fi
echo ""

# Summary
echo "========================================"
echo "📊 DIAGNOSTIC SUMMARY"
echo "========================================"
echo ""

# Create a summary report
ISSUES_FOUND=0

if ! echo "$ENV_VARS" | grep -q "GCS_BUCKET"; then
    error "CRITICAL: GCS_BUCKET environment variable not set"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi

if ! gsutil ls gs://${BUCKET_NAME}/ &>/dev/null; then
    error "CRITICAL: GCS bucket not found"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi

if [ "$HTTP_CODE" != "200" ]; then
    error "Service health check failing"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi

if [ "$REQ_TIMEOUT" -lt 600 ]; then
    warning "Timeout may be too short for large documents"
fi

if [ "$RECENT_ERRORS" -gt 5 ]; then
    warning "Multiple errors in recent logs"
fi

echo ""
if [ "$ISSUES_FOUND" -eq 0 ]; then
    success "No critical issues found!"
    info "If you're still experiencing problems, check application logs:"
    echo "   gcloud run services logs tail $SERVICE_NAME --region=$REGION"
else
    error "Found $ISSUES_FOUND critical issue(s)"
    echo ""
    echo "🔧 Recommended fixes:"
    echo ""
    
    if ! echo "$ENV_VARS" | grep -q "GCS_BUCKET"; then
        echo "1. Set GCS_BUCKET environment variable:"
        echo "   gcloud run services update $SERVICE_NAME \\"
        echo "     --region=$REGION \\"
        echo "     --set-env-vars='GCS_BUCKET=$BUCKET_NAME'"
        echo ""
    fi
    
    if ! gsutil ls gs://${BUCKET_NAME}/ &>/dev/null; then
        echo "2. Create GCS bucket:"
        echo "   gsutil mb -p $PROJECT_ID -l $REGION gs://${BUCKET_NAME}/"
        echo ""
    fi
    
    if [ "$HTTP_CODE" != "200" ]; then
        echo "3. Check service logs for errors:"
        echo "   gcloud run services logs read $SERVICE_NAME --region=$REGION --limit=100"
        echo ""
    fi
    
    echo "4. Deploy the fixed version:"
    echo "   ./quick_fix_deploy.sh"
    echo ""
fi

echo "========================================"
echo "🎯 Next Steps"
echo "========================================"
echo ""
echo "1. Apply any recommended fixes above"
echo "2. Deploy the updated code:"
echo "   ./quick_fix_deploy.sh"
echo "3. Test with a small document"
echo "4. Monitor logs during processing:"
echo "   gcloud run services logs tail $SERVICE_NAME --region=$REGION"
echo ""
echo "========================================"
