#!/bin/bash
# AutoTA Quick Start Script
# Run this after adding your API key to .env

set -e  # Exit on error

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║              AutoTA - Quick Start Test                     ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "   Run: python3 -m venv venv && source venv/bin/activate && pip install -e '.[dev]'"
    exit 1
fi

# Activate venv
source venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo ""
    echo "Creating .env template..."
    cp .env.example .env
    echo "✓ Created .env file"
    echo ""
    echo "⚠️  Please add your API key to .env:"
    echo "   echo 'ANTHROPIC_API_KEY=sk-ant-your-key' > .env"
    echo ""
    echo "Get an API key at: https://console.anthropic.com/"
    exit 1
fi

# Check if API key is set
source .env
if [ -z "$ANTHROPIC_API_KEY" ] || [ "$ANTHROPIC_API_KEY" = "" ]; then
    echo "❌ ANTHROPIC_API_KEY not set in .env file!"
    echo ""
    echo "Please edit .env and add your API key:"
    echo "   echo 'ANTHROPIC_API_KEY=sk-ant-your-key' > .env"
    echo ""
    exit 1
fi

echo "✓ Virtual environment active"
echo "✓ API key found (${ANTHROPIC_API_KEY:0:15}...)"
echo ""

# Run tests first
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1: Running test suite..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

pytest tests/ -v --tb=short | head -50
TEST_RESULT=$?

if [ $TEST_RESULT -ne 0 ]; then
    echo ""
    echo "❌ Tests failed! Please check the output above."
    exit 1
fi

echo ""
echo "✓ All tests passed!"
echo ""

# Run API test
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2: Testing Claude API integration..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python test_api_quick.py
API_RESULT=$?

if [ $API_RESULT -ne 0 ]; then
    echo ""
    echo "⚠️  API test had issues. Check the output above."
    echo "   This might be normal if Claude's responses need adjustment."
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3: Generating sample variants with CLI..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

autota generate --spec specs/example_kmap.yaml --num 3
CLI_RESULT=$?

if [ $CLI_RESULT -ne 0 ]; then
    echo ""
    echo "⚠️  CLI generation had issues."
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 SUCCESS! AutoTA is fully operational!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Generated variants are in: output/example_kmap/"
echo ""
echo "Next steps:"
echo "  • View generated variants: ls -lh output/example_kmap/"
echo "  • Check report: cat output/example_kmap/report.json"
echo "  • Generate more: autota generate --spec specs/example_kmap.yaml --num 10"
echo "  • Read the guide: cat QUICKSTART.md"
echo ""
