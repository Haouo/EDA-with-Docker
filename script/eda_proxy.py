#!/usr/bin/env python3
import os
import sys

from pyproxy.command_builder import RemotePayloadBuilder
from pyproxy.configuration import EDAConfig
from pyproxy.environment_holder import EnvironmentHandler
from pyproxy.ssh_executor import SSHExecutor


if __name__ == "__main__":
    DEBUG = True
    # get the current tool name
    tool_name = os.path.basename(sys.argv[0])
    if tool_name.endswith(".py"):
        print(f"Do not run {tool_name} directly! Please run the symlinks.")
        sys.exit(1)

    # define classes
    config = EDAConfig(debug=DEBUG)
    env_handler = EnvironmentHandler(config)
    payload_builder = RemotePayloadBuilder(tool_name, args=sys.argv[1:])
    ssh_executor = SSHExecutor(config, debug=DEBUG)

    # get environment variable prefix
    env_prefix = env_handler.build_prefix_command(tool_name)
    # generate remote ssh command
    ssh_command = payload_builder.build(env_prefix)
    # execute the ssh command generated
    ssh_executor.run(remote_payload=ssh_command)
