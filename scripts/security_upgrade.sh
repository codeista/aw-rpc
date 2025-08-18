#!/bin/bash
# Security vulnerability fixes for AW-RPC
# Date: August 2024

echo "🔒 Applying security fixes for AW-RPC..."
echo ""

# Activate virtual environment if it exists
if [ -d "flask-env" ]; then
    source flask-env/bin/activate
fi

echo "📦 Upgrading vulnerable packages..."
echo ""

# Fix Flask vulnerability (CVE-2025-47278)
echo "1. Upgrading Flask (current: 2.3.3)..."
pip install --upgrade "Flask>=3.1.1"

# Fix Werkzeug vulnerabilities (CVE-2024-34069)
echo ""
echo "2. Upgrading Werkzeug (current: 2.3.8)..."
pip install --upgrade "Werkzeug>=3.1.0"

# Fix pip vulnerabilities
echo ""
echo "3. Upgrading pip (current: 22.0.2)..."
python -m pip install --upgrade pip

# Verify upgrades
echo ""
echo "✅ Verifying upgrades..."
echo ""
pip list | grep -E "Flask|Werkzeug|pip" | head -10

# Run security scan again
echo ""
echo "🔍 Running security scan..."
safety check || true

echo ""
echo "✅ Security upgrades complete!"
echo ""
echo "⚠️  IMPORTANT: Test the application thoroughly after these upgrades!"
echo "   Run: python run_regression_tests.py"