#!/usr/bin/env python3
import os
import sys
import shlex
import subprocess
import tomllib as toml

# ==========================
# Default configuration
# ==========================
DEFAULT_CONFIG = {
    "connection": {
        "remote_host": "eda",
        "remote_user": "aislab",
        "ssh_options": [
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "UserKnownHostsFile=/dev/null",
            "-o",
            "LogLevel=QUIET",
        ],
    },
    "eda_tools": {},
    "environment": {},
}

CONFIG_FILE = "/usr/local/bin/eda_config.toml"
DEBUG = True


def load_config() -> dict:
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
        if "eda_tools" in loaded:
            config["eda_tools"].update(loaded["eda_tools"])
        if "environment" in loaded:
            config["environment"].update(loaded["environment"])

    except Exception as e:
        if DEBUG:
            print(f"[DEBUG] Failed to load {CONFIG_FILE}: {e}", file=sys.stderr)

    return config


# ==========================
# Build remote SSH command
# ==========================
def build_ssh_command(config: dict, tool_name: str, remote_cmd: str):
    ssh_cmd = ["ssh"]

    # SSH options
    ssh_cmd += config["connection"]["ssh_options"]

    # Allocate pseudo-TTY if interactive
    if sys.stdin.isatty():
        ssh_cmd.append("-t")

    # get remote hostname and username
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

    # get the tool name
    tool_name = os.path.basename(sys.argv[0])

    # Disallow direct script execution
    if tool_name.endswith(".py"):
        print(f"Error: Do not run {tool_name} directly. Use a symlink instead.")
        sys.exit(1)

    # get current working directory path
    current_dir = os.getcwd()

    # quote arguments safely
    try:
        args_str = shlex.join(sys.argv[1:])
    except AttributeError:
        args_str = " ".join(shlex.quote(arg) for arg in sys.argv[1:])

    # get passthrough env variables
    env_conf: dict = config.get("environment", {})
    vars_to_export = set()
    current_proj = os.environ.get("CURRENT_PROJECT")
    if current_proj:
        proj_env_conf = env_conf.get(current_proj, {})
        if proj_env_conf:
            proj_vars = proj_env_conf.get("passthrough", [])
            vars_to_export.update(proj_vars)

    env_export = []
    for var in vars_to_export:
        val = os.environ.get(var)
        if val:
            env_export.append(
                f"setenv {var} {val}"
            )  # for tcsh, it must use "setenv" instead of "set" or "export"
    if tool_name in config["eda_tools"]["commands"]:
        env_export.append("setenv EDA_ENABLE 1")

    env_prefix_cmd = "; ".join(env_export)
    if env_prefix_cmd:
        env_prefix_cmd += "; "

    # check whether the tool_name is "delegate", and build remote command
    remote_cmd = (
        f"cd {shlex.quote(current_dir)} && {args_str}"
        if tool_name == "delegate"
        else f"cd {shlex.quote(current_dir)} && {tool_name} {args_str}"
    )
    remote_cmd = env_prefix_cmd + remote_cmd

    # build complete ssh command
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
