import os
import shlex
from typing import List


class RemotePayloadBuilder:
    def __init__(self, tool_name: str, args: List[str]):
        self.tool_name = tool_name
        self.args = args
        self.cwd = os.getcwd()

    def build(self, env_prefix: str) -> str:
        try:
            args_str = shlex.join(self.args)
        except AttributeError:
            args_str = " ".join(shlex.quote(arg) for arg in self.args)

        if self.tool_name == "delegate":
            cmd_body = args_str
        else:
            cmd_body = f"{self.tool_name} {args_str}"

        payload = f"{env_prefix}cd {shlex.quote(self.cwd)} && {cmd_body}"
        return payload
