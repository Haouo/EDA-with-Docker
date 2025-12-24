from __future__ import annotations

import sys
import tomllib as toml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set


@dataclass(frozen=True)
class PathConfig:
    wrapper: str = "/usr/local/bin/eda_proxy.py"
    bin_dir: str = "/usr/local/bin"


@dataclass(frozen=True)
class ConnectionConfig:
    remote_host: str = "eda"
    remote_user: str = "aislab"
    ssh_options: List[str] = field(
        default_factory=lambda: [
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "UserKnownHostsFile=/dev/null",
            "-o",
            "LogLevel=QUIET",
        ]
    )


@dataclass(frozen=True)
class ToolConfig:
    commands: Set[str] = field(default_factory=set)
    module_map: Dict[str, str] = field(default_factory=dict)

    def get_module_name(self, tool_name: str) -> str:
        return self.module_map.get(tool_name, "")


@dataclass(frozen=True)
class EnvironmentConfig:
    # Key: Project Name, Value: List of vars
    project_map: Dict[str, Dict[str, List[str]]] = field(default_factory=dict)

    def get_passthrough_vars(self, project_name: Optional[str]) -> Set[str]:
        if not project_name or project_name not in self.project_map:
            return set()
        return set(self.project_map[project_name].get("passthrough", []))


@dataclass
class EDAConfig:
    path: PathConfig
    connection: ConnectionConfig
    tools: ToolConfig
    environment: EnvironmentConfig
    debug: bool = False

    @classmethod
    def load(cls, path: Path, debug: bool = False) -> EDAConfig:
        defaults = cls(
            path=PathConfig(),
            connection=ConnectionConfig(),
            tools=ToolConfig(),
            environment=EnvironmentConfig(),
        )

        if not path.exists():
            return defaults

        try:
            with path.open("rb") as f:
                data = toml.load(f)

            # Unpacking nested dicts into Dataclasses (Simple Mapping)
            path_data = data.get("path", {})
            conn_data = data.get("connection", {})
            tool_data = data.get("eda_tools", {})
            env_data = data.get("environment", {})

            return cls(
                path=PathConfig(**path_data) if path_data else defaults.path,
                connection=ConnectionConfig(**conn_data)
                if conn_data
                else defaults.connection,
                tools=ToolConfig(**tool_data) if tool_data else defaults.tools,
                environment=EnvironmentConfig(project_map=env_data),
                debug=debug,
            )
        except Exception as e:
            if debug:
                print(f"[Config Error] {e}", file=sys.stderr)
            return defaults
