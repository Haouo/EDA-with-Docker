import os
import sys
from typing import Dict

# Try importing tomllib (Python 3.11+) or fallback to toml
try:
    import tomllib as toml
except ImportError:
    try:
        import toml
    except ImportError:
        print("Error: 'tomllib' (Python 3.11+) or 'toml' package is required.")
        sys.exit(1)


class EDAConfig:
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
        "eda_tools": {"commands": []},
        "environment": {},
    }

    def __init__(
        self, config_path: str = "/usr/local/bin/eda_config.toml", debug: bool = False
    ):
        self.config_path = config_path
        self.debug = debug
        self._data = self._load_config()

    def _load_config(self) -> Dict:
        config = self.DEFAULT_CONFIG.copy()

        if not os.path.exists(self.config_path):
            return config

        try:
            with open(self.config_path, "rb") as f:
                loaded = toml.load(f)
                # Shallow merge
                for section in ["connection", "eda_tools", "environment"]:
                    if section in loaded:
                        config[section].update(loaded[section])
        except Exception as e:
            if self.debug:
                print(
                    f"[DEBUG] Failed to load {self.config_path}: {e}", file=sys.stderr
                )

        return config

    @property
    def connection(self) -> Dict:
        return self._data["connection"]

    @property
    def environment(self) -> Dict:
        return self._data["environment"]

    @property
    def tools(self) -> Dict:
        return self._data["eda_tools"]
