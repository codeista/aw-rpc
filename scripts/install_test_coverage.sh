#!/bin/bash
# Install test coverage tools for AW-RPC

echo "📦 Installing test coverage tools..."

# Activate virtual environment if it exists
if [ -d "flask-env" ]; then
    source flask-env/bin/activate
fi

# Install pytest-cov for coverage reports
pip install pytest-cov

# Install coverage for additional analysis
pip install coverage

# Install pytest-html for HTML test reports
pip install pytest-html

# Install pytest-benchmark for performance testing
pip install pytest-benchmark

# Install locust for load testing
pip install locust

# Install memory-profiler for memory testing
pip install memory-profiler

# Install safety for security scanning
pip install safety

echo "✅ Test coverage tools installed successfully!"
echo ""
echo "Usage examples:"
echo "  Coverage report: pytest --cov=. --cov-report=html --cov-report=term"
echo "  HTML test report: pytest --html=report.html"
echo "  Performance tests: pytest --benchmark-only"
echo "  Security scan: safety check"
echo ""