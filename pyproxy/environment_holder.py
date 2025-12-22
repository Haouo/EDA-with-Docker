import os
import shlex
from typing import Set

from .configuration import EDAConfig


class EnvironmentHandler:
    def __init__(self, config: EDAConfig):
        self.config = config

    def get_whitelist_vars(self) -> Set[str]:
        env_conf = self.config.environment
        vars_to_export = set()

        current_proj = os.environ.get("CURRENT_PROJECT")
        if current_proj:
            proj_env_conf = env_conf.get(current_proj, {})
            vars_to_export.update(proj_env_conf.get("passthrough", []))

        return vars_to_export

    def build_prefix_command(self, tool_name: str) -> str:
        export_cmds = []

        for var in self.get_whitelist_vars():
            val = os.environ.get(var)
            if val:
                export_cmds.append(f"setenv {var} {shlex.quote(val)}")

        if tool_name in self.config.tools.get("commands", []):
            export_cmds.append("setenv EDA_ENABLE 1")

        if not export_cmds:
            return ""

        return "; ".join(export_cmds) + "; "
