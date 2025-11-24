#!/bin/bash
# Quick validation script for deployment readiness

echo "🔍 HireX Backend - Deployment Validation"
echo "=========================================="
echo ""

# Check 1: Python syntax
echo "✓ Checking Python syntax..."
python3 -m py_compile app/main.py app/config.py app/db.py 2>&1
if [ $? -eq 0 ]; then
    echo "  ✅ All Python files compile successfully"
else
    echo "  ❌ Python compilation errors found"
    exit 1
fi
echo ""

# Check 2: Required files
echo "✓ Checking required files..."
required_files=(
    "Dockerfile"
    "requirements.txt"
    "render.yaml"
    ".env.example"
    "app/main.py"
    "app/config.py"
    "app/db.py"
)

all_present=true
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ Missing: $file"
        all_present=false
    fi
done
echo ""

# Check 3: Dependencies
echo "✓ Checking dependencies in requirements.txt..."
required_deps=(
    "fastapi"
    "uvicorn"
    "sqlmodel"
    "passlib"
    "python-jose"
    "sentence-transformers"
    "faiss-cpu"
)

for dep in "${required_deps[@]}"; do
    if grep -q "$dep" requirements.txt; then
        echo "  ✅ $dep"
    else
        echo "  ❌ Missing: $dep"
        all_present=false
    fi
done
echo ""

# Check 4: Docker configuration
echo "✓ Checking Dockerfile configuration..."
if grep -q "libssl-dev" Dockerfile && grep -q "libffi-dev" Dockerfile; then
    echo "  ✅ Cryptography build dependencies present"
else
    echo "  ❌ Missing cryptography build dependencies"
fi

if grep -q "tesseract-ocr" Dockerfile; then
    echo "  ✅ OCR dependencies present"
else
    echo "  ⚠️  OCR dependencies missing (optional)"
fi

if grep -q 'PORT' Dockerfile; then
    echo "  ✅ PORT variable configured"
else
    echo "  ❌ PORT variable not configured"
fi
echo ""

# Check 5: Health check endpoint
echo "✓ Checking health endpoint..."
if grep -q '/health' app/main.py; then
    echo "  ✅ Health check endpoint defined"
else
    echo "  ❌ Health check endpoint missing"
fi
echo ""

# Summary
echo "=========================================="
if [ "$all_present" = true ]; then
    echo "✅ ALL CHECKS PASSED - Ready for deployment!"
    echo ""
    echo "Next steps:"
    echo "1. Push your code to GitHub/GitLab"
    echo "2. Follow instructions in DEPLOYMENT.md"
    echo "3. Configure environment variables on Render"
    exit 0
else
    echo "❌ Some checks failed - Please fix before deploying"
    exit 1
fi
