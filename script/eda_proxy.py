#!/usr/bin/env python3
import os
import sys
import shlex
import subprocess

# ==========================
# Default configuration
# ==========================
DEFAULT_CONFIG = {
    "connection": {
        "remote_host": "eda",
        "remote_user": "aislab",
        "ssh_options": [
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", "LogLevel=QUIET",
        ]
    },
    "tools": {
        "gui_tools": ["verdi", "dve", "nWave", "design_vision", "icc2_gui"],
    }
}

CONFIG_FILE = "/usr/local/bin/eda_config.toml"
DEBUG = False

# ==========================
# Load TOML (optional)
# ==========================
try:
    import tomllib as toml  # Python >=3.11
except ImportError:
    try:
        import toml  # pip install toml
    except ImportError:
        toml = None

def load_config():
    """Load user config, fallback to DEFAULT_CONFIG."""
    config = DEFAULT_CONFIG.copy()

    if not (toml and os.path.exists(CONFIG_FILE)):
        return config

    try:
        with open(CONFIG_FILE, "rb") as f:
            loaded = toml.load(f)

        # shallow merge
        if "connection" in loaded:
            config["connection"].update(loaded["connection"])
        if "tools" in loaded:
            config["tools"].update(loaded["tools"])

    except Exception as e:
        if DEBUG:
            print(f"[DEBUG] Failed to load {CONFIG_FILE}: {e}", file=sys.stderr)

    return config


# ==========================
# Build remote SSH command
# ==========================
def build_ssh_command(config, tool_name, remote_cmd):
    ssh_cmd = ["ssh"]

    # SSH options
    ssh_cmd += config["connection"]["ssh_options"]

    # Allocate pseudo-TTY if interactive
    if sys.stdin.isatty():
        ssh_cmd.append("-t")

    # GUI 工具 => X11 forwarding
    if tool_name in config["tools"].get("gui_tools", []):
        ssh_cmd.append("-Y")

    remote_user = config["connection"]["remote_user"]
    remote_host = config["connection"]["remote_host"]
    ssh_cmd.append(f"{remote_user}@{remote_host}")

    # Append actual remote command
    ssh_cmd.append(remote_cmd)

    return ssh_cmd


# ==========================
# Main logic
# ==========================
def main():
    config = load_config()

    tool_name = os.path.basename(sys.argv[0])

    # Disallow direct script execution
    if tool_name.endswith(".py"):
        print(f"Error: Do not run {tool_name} directly. Use a symlink instead.")
        sys.exit(1)

    current_dir = os.getcwd()

    # quote arguments safely
    try:
        args_str = shlex.join(sys.argv[1:])
    except AttributeError:
        args_str = " ".join(shlex.quote(arg) for arg in sys.argv[1:])

    # Build remote command
    remote_cmd = f"cd {shlex.quote(current_dir)} && {tool_name} {args_str}"

    ssh_cmd = build_ssh_command(config, tool_name, remote_cmd)

    if DEBUG:
        print("[DEBUG] SSH command:", ssh_cmd)

    try:
        rc = subprocess.call(ssh_cmd)
        sys.exit(rc)

    except KeyboardInterrupt:
        # Let SSH handle Ctrl-C as signal
        sys.exit(130)

    except Exception as e:
        print(f"Fatal Wrapper Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

