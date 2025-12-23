import os

import pytest

from pyproxy.builder import RemotePayloadBuilder
from pyproxy.config import (
    ConnectionConfig,
    EDAConfig,
    EnvironmentConfig,
    PathConfig,
    ToolConfig,
)
from pyproxy.shell_strategies import BashStrategy, TcshStrategy


@pytest.fixture
def mock_config():
    return EDAConfig(
        path=PathConfig(),
        connection=ConnectionConfig(),
        tools=ToolConfig(commands={"vcs", "verdi"}),
        environment=EnvironmentConfig(
            project_map={"cva6": {"passthrough": ["PROJ_ROOT", "RISCV"]}}
        ),
        debug=True,
    )


def test_builder_tcsh_payload(mock_config, monkeypatch):
    """Test Tcsh shell strategy"""
    monkeypatch.setenv("CURRENT_PROJECT", "cva6")
    monkeypatch.setenv("PROJ_ROOT", "/work/cva6")
    monkeypatch.setenv("RISCV", "/opt/riscv")

    strategy = TcshStrategy()
    builder = RemotePayloadBuilder(mock_config, strategy)

    payload = builder.with_passthrough_env().build("vcs", ["-full64"])

    assert "setenv PROJ_ROOT /work/cva6" in payload
    assert "setenv RISCV /opt/riscv" in payload
    assert f"cd {shlex_quote(os.getcwd())}" in payload
    assert "vcs -full64" in payload


def test_builder_bash_payload(mock_config, monkeypatch):
    """Test Bash shell strategy"""
    monkeypatch.setenv("CURRENT_PROJECT", "cva6")
    monkeypatch.setenv("PROJ_ROOT", "/work/cva6")
    monkeypatch.setenv("RISCV", "/opt/riscv")

    strategy = BashStrategy()
    builder = RemotePayloadBuilder(config=mock_config, shell=strategy)
    payload = builder.with_passthrough_env().build("dv", [])

    assert "export PROJ_ROOT=/work/cva6" in payload
    assert "export RISCV=/opt/riscv" in payload
    assert f"cd {shlex_quote(os.getcwd())}" in payload
    assert "dv" in payload


def test_builder_delegate_mode(mock_config):
    strategy = TcshStrategy()
    builder = RemotePayloadBuilder(mock_config, strategy)

    payload = builder.build("delegate", ["ls", "-la"])

    assert "cd " in payload
    assert payload.endswith("ls -la")
    assert "delegate" not in payload.split("&&")[-1]


def shlex_quote(s):
    import shlex

    return shlex.quote(s)
