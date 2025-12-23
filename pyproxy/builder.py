from __future__ import annotations

import shlex
import os
from typing import List

from .config import AppConfig
from .strategies import ShellStrategy


class RemotePayloadBuilder:
    def __init__(self, config: AppConfig, shell: ShellStrategy):
        self.config = config
        self.shell = shell
        self._env_cmds: List[str] = []

    def with_passthrough_env(self) -> RemotePayloadBuilder:
        """Injects environment variables based on CURRENT_PROJECT"""
        current_proj = os.environ.get("CURRENT_PROJECT")
        vars_to_export = self.config.environment.get_passthrough_vars(current_proj)

        for var in vars_to_export:
            val = os.environ.get(var)
            if val is not None:
                self._env_cmds.append(self.shell.set_env(var, val))
        return self

    def with_eda_enable(self, tool_name: str) -> RemotePayloadBuilder:
        """Injects EDA_ENABLE flag if applicable"""
        if tool_name in self.config.tools.commands:
            self._env_cmds.append(self.shell.set_env("EDA_ENABLE", "1"))
        return self

    def build(self, tool_name: str, args: List[str]) -> str:
        """Constructs the final remote command string"""
        cwd = os.getcwd()

        # 1. Path Switching
        cd_cmd = f"cd {shlex.quote(cwd)}"

        # 2. Tool Execution
        args_str = shlex.join(args)
        if tool_name == "delegate":
            exec_cmd = args_str
        else:
            exec_cmd = f"{tool_name} {args_str}"

        # 3. Chain Everything
        # Sequence: [Env Vars] -> [CD] -> [Exec]
        # Note: Using '&&' logic for the final execution step in chain is strategy dependent
        # but here we simplify by letting the strategy chain them (likely via ';')

        full_sequence = self._env_cmds + [cd_cmd, exec_cmd]
        return self.shell.chain_commands(full_sequence)
