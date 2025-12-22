import subprocess
import sys

from .configuration import EDAConfig


class SSHExecutor:
    def __init__(self, config: EDAConfig, debug: bool = False):
        self.config = config
        self.debug = debug

    def run(self, remote_payload: str):
        conn_conf = self.config.connection

        ssh_cmd = ["ssh"]
        ssh_cmd += conn_conf.get("ssh_options", [])

        # TTY Check
        if sys.stdin.isatty():
            ssh_cmd.append("-t")

        target = f"{conn_conf['remote_user']}@{conn_conf['remote_host']}"
        ssh_cmd.append(target)
        ssh_cmd.append(remote_payload)

        if self.debug:
            print(f"[DEBUG] SSH command: {ssh_cmd}")

        try:
            rc = subprocess.call(ssh_cmd)
            sys.exit(rc)
        except KeyboardInterrupt:
            sys.exit(130)
        except Exception as e:
            print(f"Wrapper Error: {e}", file=sys.stderr)
            sys.exit(1)
