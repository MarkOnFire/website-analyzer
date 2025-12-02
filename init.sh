#!/bin/bash
# init.sh - Reproducible environment setup for website-analyzer
# Run this script at the start of each development session to verify environment readiness

set -e  # Exit on error

echo "=================================================="
echo "Website Analyzer - Environment Initialization"
echo "=================================================="
echo ""

# Color output helpers
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

success() {
    echo -e "${GREEN}✓${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
}

warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check Python 3.11
echo "Checking Python 3.11..."
if command -v python3.11 &> /dev/null; then
    PYTHON_VERSION=$(python3.11 --version 2>&1 | cut -d' ' -f2)
    success "Python 3.11 found: $PYTHON_VERSION"
else
    error "Python 3.11 not found. Please install Python 3.11."
    echo "  macOS: brew install python@3.11"
    echo "  Linux: apt install python3.11"
    exit 1
fi

# Check Node.js 18+
echo "Checking Node.js..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -ge 18 ]; then
        success "Node.js found: $(node --version)"
    else
        error "Node.js 18+ required. Found: $(node --version)"
        echo "  Please install Node.js 18 or higher."
        exit 1
    fi
else
    error "Node.js not found. Please install Node.js 18+."
    echo "  macOS: brew install node"
    echo "  Linux: Install via NodeSource or nvm"
    exit 1
fi

# Create/activate Python virtual environment
echo ""
echo "Setting up Python virtual environment..."
if [ ! -d ".venv" ]; then
    echo "  Creating .venv..."
    python3.11 -m venv .venv
    success "Virtual environment created"
else
    success "Virtual environment exists"
fi

# Activate virtual environment
source .venv/bin/activate
success "Virtual environment activated"

# Install/upgrade Python dependencies
echo ""
echo "Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    python3.11 -m pip install --upgrade pip -q
    python3.11 -m pip install -r requirements.txt -q
    success "Python dependencies installed"
else
    warning "requirements.txt not found. Creating basic requirements..."
    cat > requirements.txt << EOF
crawl4ai>=0.7.6
playwright>=1.40.0
beautifulsoup4>=4.12.0
lxml>=5.0.0
pydantic>=2.5.0
typer>=0.9.0
rich>=13.7.0
asyncio>=3.4.3
validators>=0.22.0
tldextract>=5.1.0
litellm>=1.30.0
EOF
    python3.11 -m pip install --upgrade pip -q
    python3.11 -m pip install -r requirements.txt -q
    success "Basic requirements installed"
fi

# Install Playwright browsers
echo ""
echo "Installing Playwright browsers..."
if python3.11 -m playwright install chromium --with-deps &> /dev/null; then
    success "Playwright Chromium installed"
else
    warning "Playwright browser install failed (may already be installed)"
fi

# Install Node.js dependencies
echo ""
echo "Setting up Node.js dependencies..."
if [ -d "mcp-server" ]; then
    cd mcp-server
    if [ -f "package.json" ]; then
        npm install --silent
        success "Node.js dependencies installed"
    else
        warning "package.json not found in mcp-server/"
    fi
    cd ..
else
    warning "mcp-server/ directory not found (will be created during development)"
fi

# Verify project structure
echo ""
echo "Verifying project structure..."
mkdir -p projects
mkdir -p tests
success "Project directories ready"

# Check for feature_list.json
if [ -f "feature_list.json" ]; then
    TOTAL_FEATURES=$(grep -o '"passes": false' feature_list.json | wc -l)
    COMPLETED_FEATURES=$(grep -o '"passes": true' feature_list.json | wc -l)
    success "Feature list found: $COMPLETED_FEATURES completed, $TOTAL_FEATURES pending"
else
    warning "feature_list.json not found (should be created by initializer)"
fi

# Environment check summary
echo ""
echo "=================================================="
echo "Environment Ready!"
echo "=================================================="
echo ""
echo "Python: $(python3.11 --version)"
echo "Node.js: $(node --version)"
echo "Virtual env: $(which python)"
echo ""
echo "Next steps:"
echo "  1. Ensure .venv is activated: source .venv/bin/activate"
echo "  2. Review feature_list.json for current feature"
echo "  3. Check claude-progress.txt for session notes"
echo "  4. Begin implementation of next feature"
echo ""
