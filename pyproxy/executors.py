import shlex
import subprocess
import sys

from .config import ConnectionConfig


class SSHExecutor:
    def __init__(self, config: ConnectionConfig, debug: bool = False):
        self.config = config
        self.debug = debug

    def execute(self, remote_payload: str) -> int:
        ssh_cmd = ["ssh"]
        ssh_cmd.extend(self.config.ssh_options)

        # TTY handling
        if sys.stdin.isatty():
            ssh_cmd.append("-t")

        # "ssh command" + "target remote" + "payload"
        # the payload includes env-passthrough and other arguments from the EDA command
        target = f"{self.config.remote_user}@{self.config.remote_host}"
        ssh_cmd.append(target)
        ssh_cmd.append(remote_payload)

        if self.debug:
            print(f"[DEBUG] Executing: {shlex.join(ssh_cmd)}", file=sys.stderr)

        # Signal Handling is done implicitly by the child process,
        # but we catch it here to prevent Python tracebacks.
        try:
            return subprocess.call(ssh_cmd)
        except KeyboardInterrupt:
            # Propagate the signal semantics by exiting with 130
            return 130
