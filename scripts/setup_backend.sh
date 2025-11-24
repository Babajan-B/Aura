#!/bin/bash
# Quick setup script for AI Learning Coach backend

set -e

echo "==================================="
echo "AI Learning Coach - Backend Setup"
echo "==================================="
echo ""

# Navigate to backend directory
cd "$(dirname "$0")/../backend"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed."
    echo "Please install Python 3.9 or higher."
    exit 1
fi

echo "Step 1: Creating virtual environment..."
python3 -m venv venv

echo "Step 2: Activating virtual environment..."
source venv/bin/activate

echo "Step 3: Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "==================================="
echo "Setup Complete!"
echo "==================================="
echo ""
echo "Next steps:"
echo "1. Fill in your credentials in backend/.env"
echo "   - Supabase credentials (DATABASE_URL, SUPABASE_URL, etc.)"
echo "   - Gemini API key (GEMINI_API_KEY)"
echo ""
echo "2. Activate the virtual environment:"
echo "   cd backend"
echo "   source venv/bin/activate"
echo ""
echo "3. Run the application:"
echo "   uvicorn app.main:app --reload"
echo ""
echo "4. Visit http://localhost:8000/docs for API documentation"
echo ""
