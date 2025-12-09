#!/usr/bin/env python3

import os
import logging
from pathlib import Path
import tomllib as toml


def load_config(config_file_path: str) -> dict:
    if not os.path.exists(config_file_path):
        logging.error(f"Config file '{config_file_path}' not found.")

    try:
        with open(config_file_path, "rb") as f:
            return toml.load(f)
    except Exception as e:
        logging.error(f"Failed to parse TOML {e}")
        exit(-1)


def get_config_value(config: dict, section: str, key: str) -> str:
    try:
        return config[section][key]
    except KeyError:
        logging.error(f"Missing required config: [{section}] {key}")
        exit(-1)


def main():
    # set logger
    logging.basicConfig(level=logging.INFO)

    # load EDA config
    config = load_config("/usr/local/bin/eda_config.toml")

    # check wrapper and binary directory path
    wrapper_path = Path(get_config_value(config, "default", "wrapper_path")).resolve()
    bin_dir = Path(get_config_value(config, "default", "bin_dir")).resolve()

    # Check wrapper existence
    if not wrapper_path.exists():
        logging.error(f"Wrapper script does not exist: {wrapper_path}")
        exit(-1)

    # Check bin_dir existence (auto create)
    if not bin_dir.exists():
        logging.info(f"bin_dir does not exist. Creating: {bin_dir}")
        try:
            bin_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            logging.error(f"Permission denied creating directory: {bin_dir}")
            exit(-1)

    logging.info(f"--- Setting up EDA Symlinks in {bin_dir} ---")

    # Verify "eda_tools" structure
    if "eda_tools" not in config or not isinstance(config["eda_tools"], dict):
        logging.error("Missing or invalid [eda_tools] section in config.")
        exit(-1)

    count = 0

    for category, section in config["eda_tools"].items():
        if category != "commands":
            logging.warning("Missing 'commands' key. Skipped.")
            continue

        if not isinstance(section, list):
            logging.warning("'commands' must be a list. Skipped.")
            continue

        # setup "delegate" symlink
        os.symlink(str(wrapper_path), str(bin_dir / "delegate"))

        # setup symlinks for other commands
        for cmd in section:
            target_link = bin_dir / cmd

            # If symlink exists — remove it
            if target_link.is_symlink():
                target_link.unlink()

            # If file exists and is NOT a symlink — don't touch it
            elif target_link.exists():
                logging.warning(f"Skipping {cmd}: File exists and is not a symlink.")
                continue

            # Create symlink
            try:
                os.symlink(str(wrapper_path), str(target_link))
                logging.info(f"[{category}] Linked: {cmd} -> {wrapper_path}")
                count += 1
            except PermissionError:
                logging.warning(f"Permission denied creating symlink: {target_link}")

    logging.info(f"Done. Created/Updated {count} symlinks.")


if __name__ == "__main__":
    main()
