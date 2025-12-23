import os
import sys
from pathlib import Path

from .builder import RemotePayloadBuilder
from .config import EDAConfig
from .executors import SSHExecutor
from .shell_strategies import TcshStrategy


def run():
    # Setup
    DEBUG_MODE = os.environ.get("EDA_PROXY_DEBUG", "0") == "1"
    CONFIG_PATH = Path("/usr/local/bin/eda_config.toml")

    # 1. Initialize Configuration
    try:
        config = EDAConfig.load(CONFIG_PATH, debug=DEBUG_MODE)
    except Exception as e:
        sys.exit(f"Configuration failure: {e}")

    # 2. Validate Tool Name
    tool_path = Path(sys.argv[0])
    tool_name = tool_path.name

    if tool_path.suffix == ".py":
        sys.exit(f"Error: Do not run {tool_name} directly. Use a symlink.")

    # 3. Build Payload
    # Dependency Injection: We can easily switch to BashStrategy if needed
    shell_strategy = TcshStrategy()
    builder = RemotePayloadBuilder(config, shell_strategy)
    remote_command = builder.with_passthrough_env().build(tool_name, sys.argv[1:])

    # 4. Execute
    executor = SSHExecutor(config.connection, debug=DEBUG_MODE)
    sys.exit(executor.execute(remote_command))
