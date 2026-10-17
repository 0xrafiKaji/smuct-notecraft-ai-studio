#!/usr/bin/env bash
# ==============================================================================
# NoteCraft AI Studio — One-Click Launch Script
# SMUCT CSE & CSIT Academic Suite with Live Google Sheet Auto-Sync
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "======================================================================"
echo "  🚀 Starting NoteCraft AI Studio (SMUCT Production Suite)"
echo "======================================================================"

# Check Python3
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 is not installed on your system."
    exit 1
fi

# Ensure venv exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "⬇️  Installing required packages..."
    pip install --upgrade pip
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Ensure .env exists
if [ ! -f ".env" ]; then
    echo "⚙️ Creating .env configuration from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
    else
        cat <<EOT > .env
GEMINI_API_KEY=
PORT=8000
GOOGLE_SHEET_ID=1Dg4poYmMlhm6WDUl0XYwhgSR33BDsi7DjGCQOLqz0R0
ADMIN_PASSWORD=rafik2026
EOT
    fi
fi

PORT=${PORT:-8000}

echo ""
echo "✨ Status:"
echo "   • Environment: .env loaded"
echo "   • Google Sheet ID: 1Dg4poYmMlhm6WDUl0XYwhgSR33BDsi7DjGCQOLqz0R0"
echo "   • Local Web Server: http://localhost:$PORT"
echo "   • API Docs: http://localhost:$PORT/docs"
echo ""
echo "🌐 Open your web browser at: http://localhost:$PORT"
echo "Press Ctrl+C to stop the server."
echo "======================================================================"

uvicorn backend.main:app --host 0.0.0.0 --port "$PORT" --reload
