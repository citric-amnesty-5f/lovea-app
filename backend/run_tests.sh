#!/bin/bash

# LoveAI Backend Test Runner
# Run all tests with coverage

echo "=================================="
echo "LoveAI Backend - Test Suite"
echo "=================================="
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest not found. Installing dependencies..."
    pip install -r requirements.txt
fi

echo "Running tests..."
echo ""

# Run tests with coverage
pytest tests/ \
    -v \
    --tb=short \
    --cov=app \
    --cov-report=term-missing \
    --cov-report=html

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "=================================="
    echo "✅ All tests passed!"
    echo "=================================="
    echo ""
    echo "Coverage report generated in: htmlcov/index.html"
    echo ""
else
    echo ""
    echo "=================================="
    echo "❌ Some tests failed!"
    echo "=================================="
    echo ""
    exit 1
fi
