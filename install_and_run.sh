#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════
#  Dadyar – Judicial Decision-Making Simulator
#  Installer & Launcher Script (Linux / macOS)
# ══════════════════════════════════════════════════════════════════════
set -e

# ─── Colors ───────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ─── Project paths ───────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_ROOT/.venv"
REQUIREMENTS="$SCRIPT_DIR/requirements.txt"
ENV_FILE="$PROJECT_ROOT/.env"
ENV_EXAMPLE="$PROJECT_ROOT/.env.example"
APP_FILE="$SCRIPT_DIR/app.py"

echo -e "${CYAN}══════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  ⚖️  Dadyar – Judicial Decision-Making Simulator            ${NC}"
echo -e "${CYAN}══════════════════════════════════════════════════════════════${NC}"
echo ""

# ─── 1. Check Python ─────────────────────────────────────────────────
echo -e "${YELLOW}[1/5]${NC} Checking Python..."
if command -v python3 &>/dev/null; then
    PY=python3
elif command -v python &>/dev/null; then
    PY=python
else
    echo -e "${RED}✗ Python not found! Please install Python 3.9+${NC}"
    exit 1
fi

PY_VERSION=$($PY --version 2>&1 | awk '{print $2}')
PY_MAJOR=$($PY -c "import sys; print(sys.version_info.major)")
PY_MINOR=$($PY -c "import sys; print(sys.version_info.minor)")

if [[ "$PY_MAJOR" -lt 3 ]] || [[ "$PY_MAJOR" -eq 3 && "$PY_MINOR" -lt 9 ]]; then
    echo -e "${RED}✗ Python 3.9+ required (found $PY_VERSION)${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python $PY_VERSION${NC}"

# ─── 2. Create virtual environment ───────────────────────────────────
echo -e "${YELLOW}[2/5]${NC} Setting up virtual environment..."
if [[ ! -d "$VENV_DIR" ]]; then
    $PY -m venv "$VENV_DIR"
    echo -e "${GREEN}✓ Virtual environment created at $VENV_DIR${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi

# Activate venv
source "$VENV_DIR/bin/activate"

# ─── 3. Upgrade pip & install setuptools ──────────────────────────────
echo -e "${YELLOW}[3/5]${NC} Upgrading pip..."
pip install --upgrade pip setuptools wheel --quiet
echo -e "${GREEN}✓ pip upgraded${NC}"

# ─── 4. Install dependencies ─────────────────────────────────────────
echo -e "${YELLOW}[4/5]${NC} Installing dependencies..."
if [[ ! -f "$REQUIREMENTS" ]]; then
    echo -e "${RED}✗ requirements.txt not found at $REQUIREMENTS${NC}"
    exit 1
fi

pip install -r "$REQUIREMENTS" --quiet 2>&1 | grep -v "already satisfied" || true
echo -e "${GREEN}✓ All dependencies installed${NC}"

# ─── 5. Setup .env file ──────────────────────────────────────────────
echo -e "${YELLOW}[5/5]${NC} Checking configuration..."
if [[ ! -f "$ENV_FILE" ]]; then
    if [[ -f "$ENV_EXAMPLE" ]]; then
        cp "$ENV_EXAMPLE" "$ENV_FILE"
        echo -e "${YELLOW}⚠ Created .env from .env.example – please add your API key${NC}"
        echo -e "${YELLOW}  Edit: $ENV_FILE${NC}"
    else
        cat > "$ENV_FILE" <<'ENVEOF'
# ─── AI Provider Selection ───────────────────────────────────────────
AI_PROVIDER=gemini

# ─── OpenAI Configuration (optional if using Gemini) ─────────────────
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_TEMPERATURE=0.3
OPENAI_MAX_TOKENS=2000
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSION=1536

# ─── Gemini Configuration (free-tier) ────────────────────────────────
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-2.0-flash
GEMINI_EMBEDDING_MODEL=models/text-embedding-004
GEMINI_EMBEDDING_DIMENSION=768
ENVEOF
        echo -e "${YELLOW}⚠ Created default .env – please add your API key${NC}"
        echo -e "${YELLOW}  Edit: $ENV_FILE${NC}"
    fi
else
    echo -e "${GREEN}✓ .env already configured${NC}"
fi

# ─── Launch ──────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✓ Setup complete! Launching the application...${NC}"
echo -e "${CYAN}══════════════════════════════════════════════════════════════${NC}"
echo ""

cd "$SCRIPT_DIR"
streamlit run "$APP_FILE" --server.headless true
