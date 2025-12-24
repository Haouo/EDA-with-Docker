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
        path=PathConfig(
            wrapper="/usr/local/bin/eda_proxy.py", bin_dir="/usr/local/bin"
        ),
        connection=ConnectionConfig(
            remote_host="eda",
            remote_user="aislab",
            ssh_options=[
                "-o",
                "StrictHostKeyChecking=no",
                "-o",
                "UserKnownHostsFile=/dev/null",
                "-o",
                "LogLevel=QUIET",
            ],
        ),
        tools=ToolConfig(
            commands={
                "vcs",
                "verdi",
                "nWave",
                "dv",
                "dc_shell",
                "icc_shell",
                "icc2_shell",
                "fc_shell",
                "pt_shell",
                "fm",
                "fm_shell",
                "vc_static_shell",
                "vcf",
                "xrun",
                "innovus",
            },
            module_map={
                "vcs": "vcs",
                "verdi": "verdi",
                "nWave": "verdi",
                "dv": "synthesis",
                "dc_shell": "synthesis",
                "icc_shell": "icc",
                "icc2_shell": "icc2",
                "fc_shell": "fc",
                "pt_shell": "primetime",
                "fm": "formality",
                "fm_shell": "formality",
                "vc_static_shell": "vc-formal",
                "vcf": "vc-formal",
                "xrun": "xcelium",
                "innovus": "innovus",
            },
        ),
        environment=EnvironmentConfig(
            project_map={
                "cva6": {"passthrough": ["RISCV", "NUM_JOBS", "DV_SIMULATORS"]}
            }
        ),
        debug=True,
    )


def test_builder_tcsh_payload(mock_config, monkeypatch):
    """Test Tcsh shell strategy"""
    monkeypatch.setenv("CURRENT_PROJECT", "cva6")
    monkeypatch.setenv("RISCV", "/opt/riscv")
    monkeypatch.setenv("NUM_JOBS", "32")
    monkeypatch.setenv("DV_SIMULATORS", "veri-testharness,spike")

    strategy = TcshStrategy()
    builder = RemotePayloadBuilder(mock_config, strategy)

    payload = (
        builder.with_envmodules_enable("vcs")
        .with_passthrough_env()
        .build("vcs", ["-full64"])
    )

    assert "setenv RISCV /opt/riscv" in payload
    assert "setenv NUM_JOBS 32" in payload
    assert "setenv DV_SIMULATORS veri-testharness,spike" in payload
    assert "ml vcs" in payload
    assert f"cd {shlex_quote(os.getcwd())}" in payload
    assert "vcs -full64" in payload


def test_builder_bash_payload(mock_config, monkeypatch):
    """Test Bash shell strategy"""
    monkeypatch.setenv("CURRENT_PROJECT", "cva6")
    monkeypatch.setenv("RISCV", "/opt/riscv")
    monkeypatch.setenv("NUM_JOBS", "32")
    monkeypatch.setenv("DV_SIMULATORS", "veri-testharness,spike")

    strategy = BashStrategy()
    builder = RemotePayloadBuilder(config=mock_config, shell=strategy)
    payload = (
        builder.with_envmodules_enable("dv").with_passthrough_env().build("dv", [])
    )

    assert "export RISCV=/opt/riscv" in payload
    assert "export NUM_JOBS=32" in payload
    assert "export DV_SIMULATORS=veri-testharness,spike" in payload
    assert "ml synthesis" in payload
    assert f"cd {shlex_quote(os.getcwd())}" in payload
    assert "dv" in payload


def test_builder_delegate_mode(mock_config):
    strategy = TcshStrategy()
    builder = RemotePayloadBuilder(mock_config, strategy)

    payload = builder.build("delegate", ["make", "-j"])

    assert "cd " in payload
    assert payload.endswith("make -j")
    assert "delegate" not in payload.split("&&")[-1]


def shlex_quote(s):
    import shlex

    return shlex.quote(s)
