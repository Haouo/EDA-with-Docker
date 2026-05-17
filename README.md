# EDA with Docker

Run a full digital-IC design flow inside reproducible, isolated containers — without polluting your host, and without giving up the modern Linux toolchain you already like.

![Architecture overview](eda-with-docker.png)

---

## Table of Contents

1. [Overview](#overview)
2. [Why Two Containers?](#why-two-containers)
3. [Architecture at a Glance](#architecture-at-a-glance)
4. [Repository Layout](#repository-layout)
5. [Prerequisites](#prerequisites)
6. [Quick Start](#quick-start)
7. [Detailed Usage](#detailed-usage)
    - [1. Generate Shared SSH Keys](#1-generate-shared-ssh-keys)
    - [2. The `attach.sh` Project Manager](#2-the-attachsh-project-manager)
    - [3. Launching a New Project](#3-launching-a-new-project)
    - [4. Re-attaching to an Existing Project](#4-re-attaching-to-an-existing-project)
    - [5. Tearing Down a Project](#5-tearing-down-a-project)
8. [How EDA Commands Cross the Container Boundary](#how-eda-commands-cross-the-container-boundary)
    - [The `pyproxy` Wrapper](#the-pyproxy-wrapper)
    - [The `eda_proxy.py` Entry Point](#the-eda_proxypy-entry-point)
    - [The `setup_symlinks.py` Bootstrap](#the-setup_symlinkspy-bootstrap)
9. [Configuration Reference (`eda_config.toml`)](#configuration-reference-eda_configtoml)
10. [Per-Project Environment Variables](#per-project-environment-variables)
11. [GUI / X11 Applications](#gui--x11-applications)
12. [Development](#development)
    - [Python Environment (`uv`)](#python-environment-uv)
    - [Running the Test Suite](#running-the-test-suite)
    - [Linting and Type Checking](#linting-and-type-checking)
13. [Troubleshooting](#troubleshooting)
14. [Default Credentials](#default-credentials)

---

## Overview

Industrial EDA tools (Synopsys VCS / Design Compiler / PrimeTime, Cadence Innovus / Xcelium, Verdi, etc.) are certified on Red Hat Enterprise Linux and its derivatives, and they tend to lag the rest of the Linux ecosystem. At the same time, the open-source toolchain a typical digital-IC engineer wants — modern compilers, `fish`, `pre-commit`, recent Python, `uv`, `cmake`, `meson`, `gtkwave`, … — is much easier to consume on Ubuntu.

This project gives you both, side by side, with no host-level installation:

- An **Ubuntu 24.04** container for editing, scripting, version control, building and general development.
- A **Rocky Linux 9.3** container that hosts the EDA tools, managed via [Environment Modules](https://modules.readthedocs.io/).
- A small **wrapper layer** (`pyproxy` + `eda_proxy.py`) on the Ubuntu side that makes EDA binaries look local, while the real work happens over SSH on the Rocky side.
- A **per-project Docker volume** so each tape-out / experiment has its own isolated workspace, and multiple projects can run concurrently.

End result: you `cd` into your project on Ubuntu, type `dc_shell` or `vcs -full64` like you would on a workstation, and the wrapper takes care of selecting the right `module load`, forwarding the environment, transporting the working directory, and routing X11 back to your host.

## Why Two Containers?

| Concern | Ubuntu container | Rocky container |
|---|---|---|
| Modern dev toolchain (compilers, fish, git, python 3.14, pre-commit) | First-class | Painful on RHEL 9 |
| EDA vendor support (Synopsys / Cadence) | Unsupported, license-check fragile | Officially supported |
| Editing / scripting / build orchestration | Yes | No |
| Actually running `vcs` / `dc_shell` / `innovus` | No | Yes |

Splitting the responsibilities along this seam keeps each image small and stable, and lets you upgrade the Ubuntu side aggressively without disturbing the EDA side.

## Architecture at a Glance

```
            host (Linux + X server)
            │
            ├── /tmp/.X11-unix              ──► both containers (X11 forwarding)
            ├── /cad   (EDA installs)       ──► rocky:/cad (read-only)
            ├── /etc/hosts                  ──► rocky:/etc/hosts (license daemons)
            ├── /sys                        ──► rocky:/sys (read-only, dc_shell fix)
            └── docker volume <proj>_workspace ──► both containers at /home/aislab/workspace
                                                    (this is how the two sides share files)

  ubuntu_server (hostname: ubuntu)            rocky_server (hostname: rocky)
  ┌────────────────────────────────┐          ┌────────────────────────────────┐
  │  user: aislab, shell: fish     │          │  user: aislab, shell: tcsh     │
  │  /usr/local/bin/eda_proxy.py   │   ssh    │  sshd on :22                   │
  │  symlinks: vcs, dc_shell, ...  │ ───────► │  envmodules + EDA toolchain    │
  │  CURRENT_PROJECT=<name>        │          │  ml vcs / ml synthesis / ...   │
  └────────────────────────────────┘          └────────────────────────────────┘
                  │  bridge network "internal"  │
                  └─────────────────────────────┘
```

Key points:

- The two containers share `/home/aislab/workspace` through a **named, per-project Docker volume**. Anything you do in one is visible in the other immediately — there is no rsync, no NFS, no copy step.
- The Ubuntu side never installs EDA tools. It only ships *symlinks* that resolve to a Python wrapper, which `ssh`'s into the Rocky side.
- The Rocky side runs `sshd` as PID 1 and is the only service listening on the internal docker network.
- SSH is passwordless from Ubuntu → Rocky thanks to a key pair you generate once before the first build.

## Repository Layout

```
.
├── compose.yaml                 # Docker Compose definition for both services
├── attach.sh                    # Interactive project manager (launch / attach / teardown)
├── ubuntu/
│   ├── Dockerfile               # Ubuntu 24.04 image (dev side)
│   └── ssh_config               # Defines the `eda` SSH host alias -> rocky container
├── rocky/
│   └── Dockerfile               # Rocky Linux 9.3 image (EDA side, runs sshd)
├── pyproxy/                     # Python package: builds the remote SSH payload
│   ├── builder.py               # Assembles `ml <module>; cd <cwd>; <tool> <args>`
│   ├── config.py                # Typed dataclasses for eda_config.toml
│   ├── executors.py             # subprocess wrapper around ssh
│   ├── shell_strategies.py      # Tcsh / Bash command-chaining strategies
│   └── __init__.py
├── script/
│   ├── eda_proxy.py             # The actual entry point invoked via symlinks
│   ├── eda_config.toml          # Tools, module names, project env passthrough
│   └── setup_symlinks.py        # Generates /usr/local/bin/<tool> -> eda_proxy.py
├── tests/
│   └── test_builder.py          # pytest unit tests for payload construction
├── secrets/                     # SSH key pair shared between the two images (gitignored)
├── pyproject.toml               # uv / pytest / ruff / ty configuration
└── eda-with-docker.png          # Architecture diagram shown at the top
```

## Prerequisites

On the host you need:

- **Docker Engine** and the **Docker Compose v2** plugin (`docker compose ...`, not `docker-compose`).
- A running **X server** if you intend to launch GUI tools (`gtkwave`, `verdi`, `innovus`, …). On Linux desktops this is normally already the case; you only need `xhost` available, which `attach.sh` calls for you.
- Your licensed **EDA tool installs available at `/cad`** on the host (Synopsys / Cadence / CBDK trees). The compose file mounts `/cad` read-only into the Rocky container.
- Your **license server hostnames resolvable**. The compose file mounts the host's `/etc/hosts` read-only into the Rocky container so that license daemon lookups continue to work the same way they do on the host.

## Quick Start

```bash
# 1. Generate the SSH key pair the two images share (only the first time)
mkdir -p secrets
ssh-keygen -f ./secrets/id_ed25519 -N ''

# 2. Launch the interactive manager and pick "Launch new project"
./attach.sh
```

`attach.sh` will build the two images on first use, create a dedicated Docker volume for the project, bring the compose stack up under a project-scoped name, and drop you into a `fish` shell inside the Ubuntu container. From there:

```fish
ssh eda          # hop to the Rocky container (passwordless, alias from ubuntu/ssh_config)
vcs -full64 ...  # or just run an EDA tool directly — the wrapper handles SSH for you
```

## Detailed Usage

### 1. Generate Shared SSH Keys

Before the first build, generate an `ed25519` key pair under `./secrets/`. The build copies the **private** key into the Ubuntu image and the **public** key into the Rocky image's `~/.ssh/authorized_keys`, so SSH from Ubuntu to Rocky never asks for a password.

```bash
mkdir -p secrets
ssh-keygen -f ./secrets/id_ed25519 -N ''
```

`secrets/` is in `.gitignore` and must stay there.

### 2. The `attach.sh` Project Manager

`attach.sh` is the only command you need day-to-day. It is an interactive menu with three actions:

```
=== EDA Docker Manager ===

1) Launch new project
2) Attach to existing project
3) Turn down a project
4) Quit
```

It validates `$DISPLAY`, calls `xhost +local:docker` so the containers can talk to your X server, builds images on demand, and wires up per-project compose names and volumes.

### 3. Launching a New Project

Choosing **"Launch new project"** prompts for a project name (e.g. `cva6`, `tape_out_q3`, …) and then:

1. Builds `eda_docker_ubuntu` and `eda_docker_rocky` if they do not exist yet.
2. Creates a Docker named volume `<project>_workspace`.
3. Brings the compose stack up scoped to that project name:
   ```bash
   PROJECT_VOLUME=<project>_workspace docker compose -p <project> up -d
   ```
   This means you can run **multiple projects in parallel**; each gets its own pair of containers (`<project>-ubuntu_server-1`, `<project>-rocky_server-1`) and its own workspace volume.
4. Attaches you to the Ubuntu container with `fish`, with `DISPLAY` forwarded.

Inside the Ubuntu container, your working directory is `/home/aislab/workspace` and it is shared live with the Rocky container at the same path. Put your design files there.

### 4. Re-attaching to an Existing Project

Choosing **"Attach to existing project"** lists every container whose name matches `*ubuntu*` (running or exited), lets you pick one, starts it if needed, and `docker exec`'s you into `fish`. Use this after a reboot, or to open a second terminal into the same project.

### 5. Tearing Down a Project

Choosing **"Turn down a project"** lists currently *running* projects (derived from the running `*-ubuntu_server-1` containers), lets you pick one, and runs `docker compose down` scoped to that project. **The named volume is preserved** — you can `attach.sh` → "Attach to existing project" later and pick up where you left off, or run another launch with the same name to bring it back up. To delete a project's data permanently, follow up with `docker volume rm <project>_workspace`.

## How EDA Commands Cross the Container Boundary

The neat part of this repo is that you do **not** have to `ssh eda` manually every time you want to run an EDA tool. You can stay in the Ubuntu container and run `dc_shell`, `vcs`, `innovus` etc. as if they were installed locally. Three pieces make this work.

### The `pyproxy` Wrapper

`pyproxy/` is a small Python package responsible for assembling the command that will run on the Rocky side. It is split into single-responsibility modules so the logic stays testable:

- **`config.py`** — Strongly-typed dataclasses (`PathConfig`, `ConnectionConfig`, `ToolConfig`, `EnvironmentConfig`, `EDAConfig`) and a `load()` classmethod that reads `eda_config.toml`. On any parse error it falls back to safe defaults.
- **`shell_strategies.py`** — Strategy pattern for shell syntax. `TcshStrategy` emits `setenv X val` and joins with `;`; `BashStrategy` emits `export X=val` and joins with `&&`. Rocky's `aislab` user defaults to `tcsh`, so `TcshStrategy` is the default.
- **`builder.py`** — `RemotePayloadBuilder` composes the three pieces of a remote command:
  1. `with_passthrough_env()` — looks at `$CURRENT_PROJECT`, finds the matching `[environment.<project>]` entry in the config, and emits `setenv`/`export` lines for each variable listed under `passthrough`.
  2. `with_envmodules_enable(tool_name)` — looks the tool up in `[eda_tools.module_map]` and prepends the corresponding `ml <module>` so the right Synopsys / Cadence environment is initialised.
  3. `build(tool_name, args)` — appends `cd $PWD` and finally the tool invocation, then asks the shell strategy to chain them.
- **`executors.py`** — `SSHExecutor` invokes `ssh` with the options from `[connection]`, allocates a TTY when appropriate, and propagates the remote exit code (including 130 on Ctrl-C).

### The `eda_proxy.py` Entry Point

`script/eda_proxy.py` is the *single* script that every EDA "command" on the Ubuntu side actually runs. It:

1. Loads `eda_config.toml` from `/usr/local/bin/eda_config.toml`.
2. Reads `sys.argv[0]` to discover **which tool name it was invoked as** (this is why it must be called through a symlink — running it directly is rejected).
3. Builds the remote payload through `RemotePayloadBuilder` with `TcshStrategy`.
4. Hands the payload to `SSHExecutor`, which `ssh aislab@eda <payload>`'s it and forwards the exit code.

Set `EDA_PROXY_DEBUG=1` in the environment to see the exact `ssh` invocation on stderr.

There is one special tool name: **`delegate`**. Calling `delegate <anything>` bypasses the `ml` step entirely and just runs `<anything>` on the Rocky side. This is the escape hatch for commands that are not in `[eda_tools]` (for example, running a Makefile that internally sequences several tools).

### The `setup_symlinks.py` Bootstrap

At image build time, `script/setup_symlinks.py` runs inside the Ubuntu image and, for every entry in `[eda_tools.commands]`, creates a symlink at `/usr/local/bin/<command>` that points to `eda_proxy.py`. It also always creates the `delegate` symlink. Because each symlink shares the same target, `eda_proxy.py` can recover the intended tool name from `sys.argv[0]`. Adding a new EDA tool is therefore a one-line change to the TOML — rebuild the Ubuntu image and the symlink appears.

## Configuration Reference (`eda_config.toml`)

`script/eda_config.toml` is the single source of truth that the Ubuntu image bakes in. Schema:

```toml
[path]
wrapper = "/usr/local/bin/eda_proxy.py"   # the entry point all symlinks point to
bin_dir = "/usr/local/bin"                # where the per-tool symlinks live

[connection]
remote_host = "eda"                       # SSH alias defined in ubuntu/ssh_config
remote_user = "aislab"
ssh_options = [                           # appended verbatim to the `ssh` command line
    "-o", "StrictHostKeyChecking=no",
    "-o", "UserKnownHostsFile=/dev/null",
    "-o", "LogLevel=QUIET",
]

[eda_tools]
commands = [                              # one symlink per name will be created on Ubuntu
    "vcs", "verdi", "nWave",
    "dv", "dc_shell",
    "icc_shell", "icc2_shell", "fc_shell",
    "pt_shell",
    "fm", "fm_shell",
    "vc_static_shell", "vcf",
    "xrun",
    "innovus",
]

[eda_tools.module_map]                    # tool name  ->  envmodules module to `ml` first
vcs              = "vcs"
verdi            = "verdi"
nWave            = "verdi"
dv               = "synthesis"
dc_shell         = "synthesis"
icc_shell        = "icc"
icc2_shell       = "icc2"
fc_shell         = "fc"
pt_shell         = "primetime"
fm               = "formality"
fm_shell         = "formality"
vc_static_shell  = "vc-formal"
vcf              = "vc-formal"
xrun             = "xcelium"
innovus          = "innovus"

# Per-project environment variable passthrough (see next section)
[environment.cva6]
passthrough = ["RISCV", "NUM_JOBS", "DV_SIMULATORS"]
```

## Per-Project Environment Variables

EDA flows often rely on a fistful of environment variables that are project-specific (RISC-V toolchain root, simulator selection, parallel-job count, …). To avoid hard-coding them or polluting every shell, the proxy uses a single switch:

1. In the Ubuntu container, export `CURRENT_PROJECT=<name>` (e.g. in your project's `direnv` / `setup.sh`).
2. In `eda_config.toml`, declare which variables to forward for that project:
   ```toml
   [environment.cva6]
   passthrough = ["RISCV", "NUM_JOBS", "DV_SIMULATORS"]
   ```
3. When you now run any EDA tool, the wrapper prepends `setenv RISCV …; setenv NUM_JOBS …; setenv DV_SIMULATORS …` to the remote payload, **but only the variables listed for the active project**. Other shell variables stay on the Ubuntu side.

If `CURRENT_PROJECT` is unset, or no `[environment.<name>]` section exists, no variables are forwarded — the EDA tool gets a clean Rocky environment plus whatever `ml <module>` set up.

## GUI / X11 Applications

Both containers receive `DISPLAY` from the host and bind-mount `/tmp/.X11-unix` read-write, and `attach.sh` calls `xhost +local:docker` to grant access. This means GUI EDA tools (`verdi`, `dve`, `innovus`, `gtkwave`, `feh`, …) work transparently:

- Tools launched from the Ubuntu side via a wrapper symlink run on Rocky but their windows render on your host.
- The Rocky `sshd` is configured with `X11Forwarding yes` and `AcceptEnv DISPLAY`, so manual `ssh eda <gui-tool>` invocations also display correctly.

On a remote / headless host you will need to set up X forwarding to your laptop separately (e.g. `ssh -X` to the host, then run `attach.sh` there); the in-container side is already configured.

## Development

The Python wrapper code is set up to be developed with [`uv`](https://docs.astral.sh/uv/), and its quality gates are `pytest`, `ruff`, and `ty`.

### Python Environment (`uv`)

```bash
uv sync                          # create .venv and install runtime + dev deps
source .venv/bin/activate        # optional — `uv run` also works
```

`pyproject.toml` pins Python 3.14 and declares `pytest` as the runtime dep plus `pytest`, `ruff`, and `ty` as dev deps. The lockfile is `uv.lock`.

### Running the Test Suite

```bash
uv run pytest                    # runs tests/test_builder.py
```

`tests/test_builder.py` exercises `RemotePayloadBuilder` end-to-end with both `TcshStrategy` and `BashStrategy`, plus the special `delegate` mode. It uses `monkeypatch` to simulate `CURRENT_PROJECT` and the forwarded env vars, asserting that the assembled payload contains the right `setenv` / `export`, the right `ml <module>`, the right `cd`, and the right tool invocation.

### Linting and Type Checking

```bash
uv run ruff check .              # lint
uv run ruff format .             # auto-format
uv run ty check                  # static type checking
```

## Troubleshooting

- **`Error: DISPLAY is not set.`** — `attach.sh` aborts when `$DISPLAY` is empty. Export it (or use `ssh -X` if you're remote) before running the script.
- **`ssh: connect to host rocky port 22: Connection refused`** — the Rocky container is not running. Use `attach.sh` → "Attach to existing project" to start it, or check `docker compose -p <project> ps`.
- **EDA tool fails with a license error** — confirm `/etc/hosts` on the host resolves your license server, and that `/cad` on the host actually contains the tool installation. Both are bind-mounted into the Rocky container at startup.
- **`dc_shell` complains about `/sys`** — the compose file already mounts `/sys` read-only into Rocky to work around this; if you customised the file, make sure that mount is still present.
- **GUI window doesn't appear** — make sure `xhost +local:docker` actually ran (it's done by `attach.sh`), and that you launched a GUI-capable tool with `$DISPLAY` set inside the container.
- **Want to see what's actually being SSH'd?** — `export EDA_PROXY_DEBUG=1` in the Ubuntu container before invoking a tool. The wrapper will print the full `ssh` command line to stderr.
- **Permission errors creating symlinks at build time** — `setup_symlinks.py` runs as root during image build; if you adapted it to run inside a running container, make sure the user has write access to `bin_dir`.

## Default Credentials

For convenience, both containers ship with the same demo credentials:

- User: `aislab`
- Password: `1234`

These are fine inside an isolated, single-user dev setup but are obviously **not** suitable for a multi-tenant or networked environment. Change them in both Dockerfiles before exposing the containers beyond your machine.
