#!/bin/bash

# GitHub Actions Test Runner Script
# Runs tests with proper error handling and minimal output

set -e  # Exit on any error

echo "🧪 Starting test suite..."

# Go back to project root
cd "$(dirname "$0")/../.."

echo "🔧 Running CI environment tests..."
python3 -m pytest tests/test_ci_environment.py -q --tb=short || {
    echo "❌ CI environment tests failed"
    exit 1
}

echo "🏗️ Running project structure tests..."
python3 -m pytest tests/test_project_structure.py -q --tb=short || {
    echo "❌ Project structure tests failed"
    exit 1
}

echo "📊 Running database connection tests (local PostgreSQL)..."
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/test_db"
python3 -m pytest tests/database/test_connection.py -q --tb=short -m "not integration" || {
    echo "❌ Local database tests failed"
    exit 1
}

echo "🔗 Running database integration tests (Supabase)..."
if [ -n "$SUPABASE_URL" ]; then
    export DATABASE_URL="$SUPABASE_URL"
    python3 -m pytest tests/database/test_connection.py -q --tb=short -m "integration" || {
        echo "⚠️  Supabase integration tests failed (continuing...)"
    }
else
    echo "⏭️ Skipping Supabase integration tests (no SUPABASE_URL)"
fi

echo "🔄 Running data processing tests..."
python3 -m pytest tests/pipeline/test_data_processing.py -q --tb=short || {
    echo "❌ Data processing tests failed"
    exit 1
}

echo "🚀 Running full pipeline integration test..."
python3 -m pytest tests/pipeline/test_full_pipeline.py -q --tb=short || {
    echo "❌ Pipeline integration test failed"
    exit 1
}

echo "🎨 Running visualization tests..."
python3 -m pytest tests/visualization/ -q --tb=short || {
    echo "❌ Visualization tests failed"
    exit 1
}

echo "✅ All tests passed successfully!"