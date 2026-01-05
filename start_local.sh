#!/bin/bash
# start_local.sh - Start the IPO Compliance System locally

echo "🚀 Starting IPO Compliance System (Local Mode)"
echo "================================================"

# Check if .env-local exists
if [ ! -f ".env-local" ]; then
    echo "❌ Error: .env-local file not found!"
    echo "Please create .env-local file with your configuration"
    exit 1
fi

# Check if uploads and storage directories exist
mkdir -p uploads storage
echo "✅ Created uploads and storage directories"

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "🐍 Python version: $python_version"

# Install/update dependencies
echo ""
echo "📦 Installing dependencies..."
pip install -r requirements-local.txt --quiet

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed"

# Test Neo4j connection
echo ""
echo "🔌 Testing Neo4j connection..."
python3 << EOF
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv('.env-local')

uri = os.getenv('NEO4J_URI')
user = os.getenv('NEO4J_USER')
password = os.getenv('NEO4J_PASSWORD')

try:
    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        result = session.run("RETURN 1 as test")
        print("✅ Neo4j connection successful")
    driver.close()
except Exception as e:
    print(f"❌ Neo4j connection failed: {e}")
    exit(1)
EOF

if [ $? -ne 0 ]; then
    echo "❌ Neo4j connection test failed"
    echo "Please check your NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD in .env-local"
    exit 1
fi

# Test AI provider
echo ""
echo "🤖 Testing AI provider..."
python3 << EOF
import os
from dotenv import load_dotenv

load_dotenv('.env-local')

ai_provider = os.getenv('AI_PROVIDER', 'openai').lower()
print(f"   Provider: {ai_provider}")

if ai_provider == 'openai':
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key or api_key.startswith('sk-proj-') == False:
        print("⚠️  Warning: OPENAI_API_KEY may be invalid")
    else:
        print("✅ OpenAI API key configured")
elif ai_provider == 'anthropic':
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        exit(1)
    else:
        print("✅ Anthropic API key configured")
elif ai_provider == 'ollama':
    ollama_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    print(f"✅ Ollama configured at {ollama_url}")
EOF

# Start the server
echo ""
echo "================================================"
echo "🎯 Starting Flask server..."
echo "================================================"
echo ""

export FLASK_ENV=development
export FLASK_APP=main_local.py

python3 main_local.py
