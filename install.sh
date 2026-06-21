#!/usr/bin/env bash
# Install system EDA tools + Python venv for AIfordebugging.
# Target: WSL Ubuntu / Debian-based Linux. See docs/SETUP.md for manual steps.
#
# Usage:
#   chmod +x install.sh
#   ./install.sh
#
# Options:
#   --optional-solvers   Also install boolector and yices2 (apt)
#   --recreate-venv      Delete .venv and create a fresh virtualenv
#   --skip-apt           Only (re)install Python deps into .venv
#   --skip-venv          Only install apt packages (no pip / venv)
#   -h, --help           Show this help

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

INSTALL_OPTIONAL_SOLVERS=false
RECREATE_VENV=false
SKIP_APT=false
SKIP_VENV=false

usage() {
  sed -n '3,14p' "$0" | sed 's/^# \{0,1\}//'
  exit 0
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --optional-solvers) INSTALL_OPTIONAL_SOLVERS=true ;;
    --recreate-venv)    RECREATE_VENV=true ;;
    --skip-apt)         SKIP_APT=true ;;
    --skip-venv)        SKIP_VENV=true ;;
    -h|--help)          usage ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      ;;
  esac
  shift
done

log() { printf '==> %s\n' "$*"; }
warn() { printf 'warning: %s\n' "$*" >&2; }

if ! command -v apt-get >/dev/null 2>&1; then
  echo "error: apt-get not found. This script expects WSL Ubuntu or Debian/Ubuntu Linux." >&2
  echo "       On other systems, install tools manually — see docs/SETUP.md" >&2
  exit 1
fi

APT_PACKAGES=(
  git
  make
  curl
  python3
  python3-venv
  python3-pip
  iverilog
  gtkwave
  yosys
  symbiyosys
  z3
  docker.io
)

install_apt() {
  if ! command -v sudo >/dev/null 2>&1; then
    echo "error: sudo is required to install system packages." >&2
    exit 1
  fi

  log "Updating apt package lists..."
  sudo apt-get update

  log "Installing EDA and runtime packages: ${APT_PACKAGES[*]}"
  sudo apt-get install -y "${APT_PACKAGES[@]}"

  # Docker Compose v2 plugin (CVDP harness uses \`docker compose\`).
  if ! docker compose version >/dev/null 2>&1; then
    if apt-cache show docker-compose-plugin >/dev/null 2>&1; then
      log "Installing docker-compose-plugin..."
      sudo apt-get install -y docker-compose-plugin
    elif apt-cache show docker-compose >/dev/null 2>&1; then
      warn "docker-compose-plugin unavailable; installing docker-compose (v1)."
      sudo apt-get install -y docker-compose
    else
      warn "Could not install Docker Compose. Install it manually for CVDP runs."
    fi
  fi

  if $INSTALL_OPTIONAL_SOLVERS; then
    log "Installing optional formal solvers (boolector, yices2)..."
    sudo apt-get install -y boolector yices2
  fi

  if ! groups "$USER" | grep -q '\bdocker\b'; then
    warn "User '$USER' is not in the docker group."
    warn "Run: sudo usermod -aG docker \"$USER\"  then log out and back in (or: newgrp docker)."
  fi

  if yosys -V 2>&1 | grep -q 'Yosys 0.9'; then
    warn "Ubuntu apt ships Yosys 0.9; SymbiYosys formal may need a newer YosysHQ build."
    warn "See docs/SETUP.md section \"Upgrade Yosys for SymbiYosys\" if sby fails on hierarchy -smtcheck."
  fi
}

setup_venv() {
  if $RECREATE_VENV && [[ -d "$ROOT/.venv" ]]; then
    log "Removing existing .venv..."
    rm -rf "$ROOT/.venv"
  fi

  if [[ ! -d "$ROOT/.venv" ]]; then
    log "Creating Python virtualenv at .venv ..."
    python3 -m venv "$ROOT/.venv"
  else
    log "Using existing .venv ..."
  fi

  # shellcheck disable=SC1091
  source "$ROOT/.venv/bin/activate"

  log "Upgrading pip and installing requirements.txt ..."
  python -m pip install -U pip
  python -m pip install -r "$ROOT/requirements.txt"
}

verify_install() {
  log "Verifying installs..."
  local failed=false

  check_cmd() {
    if command -v "$1" >/dev/null 2>&1; then
      printf '  OK  %s\n' "$1"
    else
      printf '  FAIL %s (not on PATH)\n' "$1" >&2
      failed=true
    fi
  }

  check_cmd iverilog
  check_cmd vvp
  check_cmd yosys
  check_cmd sby
  check_cmd z3
  check_cmd docker

  if docker compose version >/dev/null 2>&1; then
    printf '  OK  docker compose\n'
  elif command -v docker-compose >/dev/null 2>&1; then
    printf '  OK  docker-compose\n'
  else
    printf '  FAIL docker compose (needed for CVDP)\n' >&2
    failed=true
  fi

  # shellcheck disable=SC1091
  source "$ROOT/.venv/bin/activate"
  if python -c "import httpx, mcp, vcdvcd; print('  OK  python packages (httpx, mcp, vcdvcd)')"; then
    :
  else
    failed=true
  fi

  if python -c "import cursor_sdk" 2>/dev/null; then
    printf '  OK  cursor-sdk\n'
  else
    warn "cursor-sdk import failed (optional until --use-cursor-sdk)."
  fi

  if $failed; then
    echo "error: One or more checks failed." >&2
    exit 1
  fi

  log "Install complete."
  cat <<EOF

Next steps:
  source .venv/bin/activate
  export CURSOR_API_KEY="cursor_..."    # for --use-cursor-sdk

  # ChipBench smoke (single problem)
  PYTHONPATH=. python -m react.react_runner --prob-id Prob001 \\
    --prompt "third_party/ChipBench/Verilog Debugging/dataset_debug_one_shot_arithmetic/Prob001_continuous_input_sequence_detect_prompt.txt" \\
    --testbench "third_party/ChipBench/Verilog Debugging/dataset_debug_one_shot_arithmetic/Prob001_continuous_input_sequence_detect_test.sv" \\
    --ref "third_party/ChipBench/Verilog Debugging/dataset_debug_one_shot_arithmetic/Prob001_continuous_input_sequence_detect_ref.sv"

  # CVDP: build sim image once (see third_party/cvdp/cvdp_benchmark/)
  # Optional HF fixer: pip install -r requirements-veridebug-hf.txt

EOF
}

if ! $SKIP_APT; then
  install_apt
fi

if ! $SKIP_VENV; then
  setup_venv
  verify_install
elif ! $SKIP_APT; then
  log "Skipped venv (--skip-venv). Run without --skip-venv to install Python deps."
fi
