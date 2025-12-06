#!/usr/bin/env python3
import os
import sys
import subprocess
import shlex

# --- 預設設定 (當找不到 TOML 時使用) ---
DEFAULT_CONFIG = {
    "connection": {
        "remote_host": "eda",
        "remote_user": "aislab"
    },
    "tools": {
        "commands": ["verdi", "dve", "nWave", "design_vision", "icc2_gui"]
    }
}
CONFIG_FILE = "/usr/local/bin/eda_config.toml"
DEBUG = False
# ------------------------------------

# 嘗試載入 TOML 模組
try:
    import tomllib as toml  # Python 3.11+ 內建
except ImportError:
    try:
        import toml  # 需要 pip install toml
    except ImportError:
        toml = None

def load_config():
    """讀取設定檔，如果失敗則回傳預設值"""
    config = DEFAULT_CONFIG
    
    if toml and os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "rb") as f:
                loaded = toml.load(f)
                # 簡單的字典合併 (Deep merge 較複雜，這裡做淺層合併即可)
                if "connection" in loaded:
                    config["connection"].update(loaded["connection"])
                if "tools" in loaded:
                    config["tools"].update(loaded["tools"])
        except Exception as e:
            if DEBUG:
                print(f"[Warning] Failed to load config: {e}", file=sys.stderr)
    
    return config

def main():
    # 1. 初始化設定
    config = load_config()
    remote_host = config["connection"]["remote_host"]
    remote_user = config["connection"]["remote_user"]
    gui_tools = config["tools"]["gui_commands"]

    # 2. 判斷工具名稱
    tool_name = os.path.basename(sys.argv[0])
    
    # 防止直接執行 .py
    if tool_name.endswith('.py'):
        print(f"Error: Do not run {tool_name} directly. Please symlink tools (e.g., vcs) to it.")
        sys.exit(1)

    # 3. 準備 SSH 指令
    ssh_cmd = ["ssh"]

    # [Docker SSH 優化] 
    # 關閉 Host Key 檢查，防止 Container 重建後 IP 變動導致 SSH 報錯
    ssh_cmd.extend(["-o", "StrictHostKeyChecking=no"])
    ssh_cmd.extend(["-o", "UserKnownHostsFile=/dev/null"])
    ssh_cmd.extend(["-o", "LogLevel=QUIET"])

    # [TTY 判斷] 互動模式 (如 dc_shell, vim) 需要 TTY
    if sys.stdin.isatty():
        ssh_cmd.append("-t")

    # [GUI 判斷] 若為圖形工具，開啟 X11 Forwarding
    if tool_name in gui_tools:
        ssh_cmd.append("-Y")

    # 加入連線目標
    ssh_cmd.append(f"{remote_user}@{remote_host}")

    # 4. 組合遠端 Payload
    # 因為兩邊路徑一致，直接取當前路徑
    current_dir = os.getcwd()

    # 處理參數 (Quoting Hell 救星)
    try:
        args_str = shlex.join(sys.argv[1:])
    except AttributeError:
        # Python < 3.8
        args_str = ' '.join(shlex.quote(x) for x in sys.argv[1:])

    # 組合：先 cd 到同一層目錄，再執行工具
    remote_command = f"cd {shlex.quote(current_dir)} && {tool_name} {args_str}"
    
    ssh_cmd.append(remote_command)

    if DEBUG:
        print(f"[DEBUG] Executing: {ssh_cmd}")

    # 5. 執行並交出控制權
    try:
        # 使用 subprocess.call 讓 SSH 接管 IO
        # 這裡不捕捉 KeyboardInterrupt，讓 SSH 通道自行傳遞信號 (因為有 -t)
        return_code = subprocess.call(ssh_cmd)
        sys.exit(return_code)

    except Exception as e:
        print(f"Wrapper Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
