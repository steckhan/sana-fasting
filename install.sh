#!/usr/bin/env bash
set -euo pipefail

# ─────────────────────────────────────────────
# Sana Health Coach — OpenClaw Agent Installer
# ─────────────────────────────────────────────

AGENT_ID="health-coach"
AGENT_NAME="Sana"
AGENT_EMOJI="🏃"

echo ""
echo "  ${AGENT_EMOJI} Sana Health Coach — Installer"
echo "  ─────────────────────────────────────"
echo ""

# 1. Detect OpenClaw
if ! command -v openclaw &>/dev/null; then
  echo "❌ OpenClaw not found. Install it first: https://github.com/openclaw/openclaw"
  exit 1
fi

OPENCLAW_DIR="${HOME}/.openclaw"
WORKSPACE_DIR="${OPENCLAW_DIR}/workspace-${AGENT_ID}"
CONFIG_FILE="${OPENCLAW_DIR}/openclaw.json"

if [ ! -f "$CONFIG_FILE" ]; then
  echo "❌ OpenClaw config not found at ${CONFIG_FILE}"
  echo "   Run 'openclaw setup' first."
  exit 1
fi

echo "✅ OpenClaw found"
echo "   Config: ${CONFIG_FILE}"
echo "   Workspace: ${WORKSPACE_DIR}"
echo ""

# 2. Create workspace
if [ -d "$WORKSPACE_DIR" ]; then
  echo "⚠️  Workspace already exists at ${WORKSPACE_DIR}"
  read -p "   Overwrite? (y/N) " -n 1 -r
  echo ""
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "   Aborted."
    exit 0
  fi
fi

mkdir -p "$WORKSPACE_DIR"

# 3. Copy files
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "📁 Copying workspace files..."

# Core files
for f in SOUL.md IDENTITY.md AGENTS.md BOOTSTRAP.md HEARTBEAT.md USER.md MEMORY.md TOOLS.md; do
  cp "${SCRIPT_DIR}/${f}" "${WORKSPACE_DIR}/${f}"
done

# Protocols
mkdir -p "${WORKSPACE_DIR}/protocols"
cp -r "${SCRIPT_DIR}/protocols/"* "${WORKSPACE_DIR}/protocols/"

# Knowledge base
mkdir -p "${WORKSPACE_DIR}/knowledge"
cp -r "${SCRIPT_DIR}/knowledge/"* "${WORKSPACE_DIR}/knowledge/"

# Tools
mkdir -p "${WORKSPACE_DIR}/tools"
cp -r "${SCRIPT_DIR}/tools/"* "${WORKSPACE_DIR}/tools/"
chmod +x "${WORKSPACE_DIR}/tools/"*.sh 2>/dev/null || true

# Memory dir
mkdir -p "${WORKSPACE_DIR}/memory"

# PDF inbox
mkdir -p "${WORKSPACE_DIR}/inbox-pdfs/incoming"
mkdir -p "${WORKSPACE_DIR}/inbox-pdfs/processed"

echo "✅ Files copied"

# 4. Set up Python venv for Withings tools
echo ""
read -p "🔧 Set up Python venv for Withings integration? (y/N) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
  echo "   Creating venv..."
  python3 -m venv "${WORKSPACE_DIR}/.venv"
  source "${WORKSPACE_DIR}/.venv/bin/activate"
  pip install --quiet withings-api requests-oauthlib
  deactivate
  echo "✅ Python venv ready"
fi

# 5. Print agent config for manual addition
echo ""
echo "─────────────────────────────────────"
echo ""
echo "📋 Add this agent to your OpenClaw config (${CONFIG_FILE})."
echo "   Under agents.list, add:"
echo ""
cat << JSONEOF
{
  "id": "${AGENT_ID}",
  "name": "${AGENT_ID}",
  "workspace": "${WORKSPACE_DIR}",
  "model": "anthropic/claude-sonnet-4-6",
  "memorySearch": {
    "enabled": true,
    "extraPaths": [
      "${WORKSPACE_DIR}/knowledge",
      "${WORKSPACE_DIR}/protocols",
      "${WORKSPACE_DIR}/memory"
    ]
  },
  "identity": {
    "name": "${AGENT_NAME}",
    "emoji": "${AGENT_EMOJI}"
  }
}
JSONEOF
echo ""
echo "─────────────────────────────────────"
echo ""
echo "Then restart OpenClaw:"
echo "  openclaw gateway restart"
echo ""
echo "Start chatting with ${AGENT_NAME} ${AGENT_EMOJI} — she'll guide you through setup!"
echo ""
