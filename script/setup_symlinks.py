#!/usr/bin/env python3
import os
import sys
import shutil
from pathlib import Path

try:
    import tomllib as toml  # Python 3.11+
except ImportError:
    try:
        import toml  # pip install toml
    except ImportError:
        print("Error: Python 'toml' module not found. Run: pip install toml")
        sys.exit(1)

CONFIG_FILE = "eda_config.toml"


def err(msg):
    print(f"[Error] {msg}")
    sys.exit(1)


def warn(msg):
    print(f"[Warning] {msg}")


def load_config():
    if not os.path.exists(CONFIG_FILE):
        err(f"Config file '{CONFIG_FILE}' not found.")

    try:
        with open(CONFIG_FILE, "rb") as f:
            return toml.load(f)
    except Exception as e:
        err(f"Failed to parse TOML: {e}")


def get_config_value(config, section, key):
    try:
        return config[section][key]
    except KeyError:
        err(f"Missing required config: [{section}] {key}")


def main():
    config = load_config()

    wrapper_path = Path(get_config_value(config, "default", "wrapper_path")).resolve()
    bin_dir = Path(get_config_value(config, "default", "bin_dir")).resolve()

    # Check wrapper existence
    if not wrapper_path.exists():
        warn(f"Wrapper script does not exist: {wrapper_path}")

    # Check bin_dir existence (auto create)
    if not bin_dir.exists():
        print(f"[Info] bin_dir does not exist. Creating: {bin_dir}")
        try:
            bin_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            err(f"Permission denied creating directory: {bin_dir}")

    print(f"--- Setting up EDA Symlinks in {bin_dir} ---")

    # Verify "tools" structure
    if "tools" not in config or not isinstance(config["tools"], dict):
        err("Missing or invalid [tools] section in config.")

    count = 0

    for category, section in config["tools"].items():
        if "commands" not in section:
            warn(f"[{category}] Missing 'commands' key. Skipped.")
            continue

        cmds = section["commands"]
        if not isinstance(cmds, list):
            warn(f"[{category}] 'commands' must be a list. Skipped.")
            continue

        for cmd in cmds:
            target_link = bin_dir / cmd

            # If symlink exists — remove it
            if target_link.is_symlink():
                target_link.unlink()

            # If file exists and is NOT a symlink — don't touch it
            elif target_link.exists():
                print(f"Skipping {cmd}: File exists and is not a symlink.")
                continue

            # Create symlink
            try:
                os.symlink(str(wrapper_path), str(target_link))
                print(f"[{category}] Linked: {cmd} -> {wrapper_path}")
                count += 1
            except PermissionError:
                err(f"Permission denied creating symlink: {target_link}")

    print(f"--- Done. Created/Updated {count} symlinks. ---")


if __name__ == "__main__":
    main()

