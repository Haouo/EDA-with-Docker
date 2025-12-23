from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Set, Optional
import tomllib as toml


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


@dataclass(frozen=True)
class EnvironmentConfig:
    # Key: Project Name, Value: List of vars
    project_map: Dict[str, Dict[str, List[str]]] = field(default_factory=dict)

    def get_passthrough_vars(self, project_name: Optional[str]) -> Set[str]:
        if not project_name or project_name not in self.project_map:
            return set()
        return set(self.project_map[project_name].get("passthrough", []))


@dataclass
class AppConfig:
    connection: ConnectionConfig
    tools: ToolConfig
    environment: EnvironmentConfig
    debug: bool = False

    @classmethod
    def load(cls, path: Path, debug: bool = False) -> AppConfig:
        defaults = cls(
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
            conn_data = data.get("connection", {})
            tool_data = data.get("eda_tools", {})
            env_data = data.get("environment", {})

            return cls(
                connection=ConnectionConfig(**conn_data)
                if conn_data
                else defaults.connection,
                tools=ToolConfig(commands=set(tool_data.get("commands", []))),
                environment=EnvironmentConfig(project_map=env_data),
                debug=debug,
            )
        except Exception as e:
            if debug:
                print(f"[Config Error] {e}", file=sys.stderr)
            return defaults
