from __future__ import annotations

import shlex
from abc import ABC, abstractmethod
from typing import List


class ShellStrategy(ABC):
    """Abstract Strategy for Shell Syntax (Tcsh vs Bash)"""

    @abstractmethod
    def set_env(self, key: str, value: str) -> str:
        pass

    @abstractmethod
    def chain_commands(self, cmds: List[str]) -> str:
        pass


class TcshStrategy(ShellStrategy):
    def set_env(self, key: str, value: str) -> str:
        return f"setenv {key} {shlex.quote(value)}"

    def chain_commands(self, cmds: List[str]) -> str:
        # Filter empty strings and join
        valid_cmds = [c for c in cmds if c]
        return "; ".join(valid_cmds)


class BashStrategy(ShellStrategy):
    def set_env(self, key: str, value: str) -> str:
        return f"export {key}={shlex.quote(value)}"

    def chain_commands(self, cmds: List[str]) -> str:
        valid_cmds = [c for c in cmds if c]
        return " && ".join(valid_cmds)
