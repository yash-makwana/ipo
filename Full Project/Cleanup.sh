#!/bin/bash

# ============================================================================
# IPO Compliance Backend - Cleanup Script
# ============================================================================
# This script removes unnecessary files to streamline your backend
# 
# IMPORTANT: Creates a backup before deleting anything
# ============================================================================

set -e  # Exit on error

echo "🧹 IPO Compliance Backend Cleanup Script"
echo "========================================"
echo ""

# Check if we're in the right directory
if [ ! -f "main_local.py" ]; then
    echo "❌ Error: main_local.py not found!"
    echo "   Please run this script from the ipo-compliance-backend directory"
    exit 1
fi

# Create backup
BACKUP_DIR="backup-before-cleanup-$(date +%Y%m%d-%H%M%S)"
echo "📦 Creating backup: $BACKUP_DIR"
mkdir -p "../$BACKUP_DIR"
cp -r . "../$BACKUP_DIR/"
echo "✅ Backup created at ../$BACKUP_DIR"
echo ""

# Confirmation
echo "⚠️  WARNING: This will delete the following:"
echo ""
echo "   📁 Old backups (backup-20251207/, backup_20251205_*/)"
echo "   📁 GCP-specific files (*_vertax.py, *_gcp_backup.py)"
echo "   📁 Old versions (*_FIXED.py, *_OPTIMIZED.py, *_local.py duplicates)"
echo "   📁 Test files (test_*.py, check_*.py, diagnose*.py)"
echo "   📁 Deployment scripts (deploy_*.sh, quick_fix_*.sh)"
echo "   📁 Cache directories (__pycache__/, __MACOSX/)"
echo "   📁 Old data (storage/*.json, uploads/*)"
echo ""
echo "   Total: ~38 files/directories"
echo ""
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Cleanup cancelled"
    exit 0
fi

echo ""
echo "🗑️  Starting cleanup..."
echo ""

# ============================================================================
# REMOVE OLD BACKUPS
# ============================================================================
echo "📁 Removing old backups..."
rm -rf backup-20251207/ backup_20251205_*/ 2>/dev/null || true
echo "   ✅ Old backups removed"

# ============================================================================
# REMOVE GCP-SPECIFIC FILES
# ============================================================================
echo "📁 Removing GCP-specific files..."
rm -f compliance_engine_vertax.py 2>/dev/null || true
rm -f embeddings_service_vertex_BACKUP.py 2>/dev/null || true
rm -f semantic_legal_search_vertex_BACKUP.py 2>/dev/null || true
rm -f db_config_gcp_backup.py 2>/dev/null || true
rm -f main.py 2>/dev/null || true  # GCP version, we use main_local.py
rm -f env.yaml 2>/dev/null || true
rm -f requirements.txt 2>/dev/null || true  # GCP version
echo "   ✅ GCP files removed"

# ============================================================================
# REMOVE DUPLICATE/OLD VERSIONS
# ============================================================================
echo "📁 Removing duplicate/old versions..."
rm -f compliance_engine_local.py 2>/dev/null || true  # Duplicate of compliance_engine.py
rm -f compliance_engine_WITH_RERANKING.py 2>/dev/null || true
rm -f compliance_engine_OPTIMIZED.py 2>/dev/null || true
rm -f embeddings_service_local.py 2>/dev/null || true  # Duplicate
rm -f semantic_legal_search_local.py 2>/dev/null || true  # Duplicate
rm -f db_config_fixed.py 2>/dev/null || true
rm -f db_config_old.py 2>/dev/null || true
rm -f main_FIXED.py 2>/dev/null || true
rm -f main_async.py 2>/dev/null || true
rm -f main_DRHP.py 2>/dev/null || true
echo "   ✅ Old versions removed"

# ============================================================================
# REMOVE TEST FILES
# ============================================================================
echo "📁 Removing test files..."
rm -f test_*.py 2>/dev/null || true
rm -f check_*.py 2>/dev/null || true
rm -f diagnose*.py 2>/dev/null || true
rm -f diagnose.sh 2>/dev/null || true
rm -f fix_neo4j.py 2>/dev/null || true
rm -f neo4j_cleanup.py 2>/dev/null || true
rm -f temp_cors_fix.py 2>/dev/null || true
rm -f create_schema.py 2>/dev/null || true
rm -f api_integration_example.py 2>/dev/null || true
rm -f api_with_real_data.py 2>/dev/null || true
rm -f async_processor.py 2>/dev/null || true
rm -f process_job.py 2>/dev/null || true
echo "   ✅ Test files removed"

# ============================================================================
# REMOVE DEPLOYMENT SCRIPTS
# ============================================================================
echo "📁 Removing deployment scripts..."
rm -f deploy_legal_embeddings.sh 2>/dev/null || true
rm -f quick_fix_deploy.sh 2>/dev/null || true
rm -f find_vertex_ai.sh 2>/dev/null || true
rm -f start_neo4j_docker.sh 2>/dev/null || true  # Can recreate with docker-compose
rm -f start_local.sh 2>/dev/null || true
echo "   ✅ Deployment scripts removed"

# ============================================================================
# REMOVE CACHE DIRECTORIES
# ============================================================================
echo "📁 Removing cache directories..."
rm -rf __pycache__/ 2>/dev/null || true
rm -rf agents/__pycache__/ 2>/dev/null || true
rm -rf __MACOSX/ 2>/dev/null || true
echo "   ✅ Cache directories removed"

# ============================================================================
# OPTIONAL: REMOVE OLD DATA (Ask user)
# ============================================================================
echo ""
read -p "Remove old storage data (storage/*.json, uploads/*)? (yes/no): " remove_data

if [ "$remove_data" = "yes" ]; then
    echo "📁 Removing old data..."
    rm -f storage/*.json 2>/dev/null || true
    rm -rf uploads/* 2>/dev/null || true
    echo "   ✅ Old data removed"
else
    echo "   ⏭️  Keeping old data"
fi

# ============================================================================
# SUMMARY
# ============================================================================
echo ""
echo "✅ Cleanup complete!"
echo ""
echo "📊 Summary:"
echo "   • Backup created: ../$BACKUP_DIR"
echo "   • Old backups: removed"
echo "   • GCP files: removed"
echo "   • Old versions: removed"
echo "   • Test files: removed"
echo "   • Deployment scripts: removed"
echo "   • Cache: removed"
if [ "$remove_data" = "yes" ]; then
    echo "   • Old data: removed"
else
    echo "   • Old data: kept"
fi
echo ""
echo "📦 Core files remaining (~20 files):"
echo "   ✅ main_local.py"
echo "   ✅ compliance_engine.py"
echo "   ✅ multi_agent_orchestrator.py"
echo "   ✅ ai_config.py"
echo "   ✅ All agent files (agents/)"
echo "   ✅ requirements-local.txt"
echo "   ✅ .env-local"
echo "   ✅ docker-compose.yml"
echo ""
echo "🎯 Next steps:"
echo "   1. Verify core files: ls -la"
echo "   2. Update .env-local with Gemini API key"
echo "   3. Install dependencies: pip install -r requirements-local.txt"
echo "   4. Start Neo4j: docker-compose up -d"
echo "   5. Run backend: python main_local.py"
echo ""

# ============================================================================
# CREATE A SUMMARY FILE
# ============================================================================
cat > CLEANUP_SUMMARY.txt << EOF
IPO Compliance Backend - Cleanup Summary
========================================
Date: $(date)
Backup Location: ../$BACKUP_DIR

Files Removed:
--------------
• Old backups: backup-20251207/, backup_20251205_*/
• GCP files: *_vertax.py, *_gcp_backup.py, main.py, env.yaml
• Old versions: *_FIXED.py, *_OPTIMIZED.py, *_local.py duplicates
• Test files: test_*.py, check_*.py, diagnose*.py
• Deployment: deploy_*.sh, quick_fix_*.sh
• Cache: __pycache__/, __MACOSX/

Core Files Remaining (~20 files):
----------------------------------
• main_local.py (entry point)
• compliance_engine.py
• multi_agent_orchestrator.py
• ai_config.py
• db_config.py
• embeddings_service.py
• semantic_legal_search.py
• reranking_service.py
• drhp_mapping.py
• document_processor.py
• state_models.py
• detailed_compliance_formatter.py
• query_classifier.py
• ingest_real_legal_data.py
• agents/ (5 files)
• requirements-local.txt
• .env-local
• docker-compose.yml

Next Steps:
-----------
1. Update .env-local with your Gemini API key
2. pip install -r requirements-local.txt
3. docker-compose up -d
4. python ingest_real_legal_data.py
5. python main_local.py

To restore from backup:
-----------------------
cp -r ../$BACKUP_DIR/* .
EOF

echo "📝 Cleanup summary saved to: CLEANUP_SUMMARY.txt"
echo ""