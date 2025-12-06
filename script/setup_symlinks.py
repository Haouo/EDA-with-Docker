#!/usr/bin/env python3
import os
import sys
import shutil

try:
    import tomllib as toml  # Python 3.11+
except ImportError:
    try:
        import toml  # pip install toml
    except ImportError:
        print("Error: Python 'toml' module not found. Run: pip install toml")
        sys.exit(1)

CONFIG_FILE = "eda_config.toml"

def main():
    if not os.path.exists(CONFIG_FILE):
        print(f"Error: Config file {CONFIG_FILE} not found.")
        sys.exit(1)

    with open(CONFIG_FILE, "rb") as f:
        config = toml.load(f)

    wrapper_path = config["default"]["wrapper_path"]
    bin_dir = config["default"]["bin_dir"]

    # check whether wrapper exists
    if not os.path.exists(wrapper_path):
        print(f"Warning: Wrapper script at {wrapper_path} does not exist yet!")

    print(f"--- Setting up EDA Symlinks in {bin_dir} ---")

    # iterate over cmd_tools list
    count = 0
    for category, section in config["tools"].items():
        for cmd in section["commands"]:
            target_link = os.path.join(bin_dir, cmd)
            
            if os.path.islink(target_link):
                os.unlink(target_link)
            elif os.path.exists(target_link):
                print(f"Skipping {cmd}: File exists and is not a symlink.")
                continue

            try:
                os.symlink(wrapper_path, target_link)
                print(f"[{category}] Linked: {cmd} -> {wrapper_path}")
                count += 1
            except PermissionError:
                print(f"Error: Permission denied creating {target_link}. Try sudo.")
                sys.exit(1)

    print(f"--- Done. Created/Updated {count} symlinks. ---")

if __name__ == "__main__":
    main()
