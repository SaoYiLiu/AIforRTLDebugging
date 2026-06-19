## Setup (WSL Ubuntu 22.04)

This project expects to run simulation + formal inside **WSL**.

### Install system packages

```bash
sudo apt update
sudo apt install -y \
  git make \
  python3 python3-venv python3-pip \
  iverilog gtkwave \
  yosys symbiyosys \
  z3
```

Optional solvers (nice-to-have):

```bash
sudo apt install -y boolector yices2
```

### Create Python venv and install Python deps

From the project root:

```bash
# If you ever see `pip`/Python version mismatches inside the venv,
# delete and recreate it:
#   rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt
```

### Verify installs

```bash
iverilog -V
vvp -V
yosys -V
sby --version
z3 --version
python -c "import mcp, vcdvcd; print('python deps ok')"
```

### Cursor SDK (optional, for automated ReAct fixing)

Set an API key so the ReAct loop can call a Cursor LLM:

```bash
export CURSOR_API_KEY="cursor_..."
```

**Transport (bridge vs REST):** `--use-cursor-sdk` talks to Cursor via the local
SDK bridge when it works (WSL, desktop). On headless Linux servers where the
bridge fails but `curl https://api.cursor.com/v1/models` succeeds, the runner
automatically falls back to the Cloud Agents REST API.

REST mode requires a GitHub repo connected in Cursor (no-repo agents are not
available on all accounts):

```bash
export CURSOR_CLOUD_REPO_URL="https://github.com/YOU/AIfordebugging"
export CURSOR_CLOUD_REPO_REF="main"   # optional
```

Or let the runner pick the first repo from `GET /v1/repositories` (cached).

```bash
# Default: try bridge, then REST
python3 react/react_runner.py ... --use-cursor-sdk

# Force REST (e.g. remote server zeus)
export CURSOR_TRANSPORT=rest
# or: --cursor-transport rest

# Force local SDK bridge only (WSL)
export CURSOR_TRANSPORT=bridge
```

### Upgrade Yosys for SymbiYosys (important)

Ubuntu 22.04 `apt install yosys` provides **Yosys 0.9**. SymbiYosys **0.6x** (including the `sby` you built from source) always runs `hierarchy -smtcheck`, which requires a **modern YosysHQ Yosys** (roughly 0.36+).

If formal fails with:

```text
ERROR: Command syntax error: Unknown option ... hierarchy -smtcheck
```

upgrade Yosys (example: build from source):

```bash
sudo apt install -y build-essential clang bison flex \
  libreadline-dev gawk tcl-dev libffi-dev git \
  pkg-config python3 zlib1g-dev

git clone https://github.com/YosysHQ/yosys
cd yosys
make -j"$(nproc)"
sudo make install

yosys -V   # should NOT print "Yosys 0.9"
```

SymbiYosys also needs Python `click` if you run `sby` from a git checkout:

```bash
source .venv/bin/activate
python -m pip install click
```

### Run the MCP server (stdio)

From the project root (inside the venv):

```bash
python mcp_server.py
```

