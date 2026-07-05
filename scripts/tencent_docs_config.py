"""腾讯文档 Open API 配置管理 — 凭证加载与账号切换。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

_SKILL_DIR = Path(__file__).resolve().parent.parent
_ENV_FILE = _SKILL_DIR / ".env"

_BASE_URL = "https://docs.qq.com/openapi"


@dataclass(frozen=True)
class TencentDocsAuth:
    """三头认证信息，绝不打印 access_token。"""

    access_token: str
    client_id: str
    open_id: str

    def as_headers(self) -> dict[str, str]:
        return {
            "Access-Token": self.access_token,
            "Client-Id": self.client_id,
            "Open-Id": self.open_id,
        }


def _parse_env_file(path: Path) -> dict[str, str]:
    """解析 .env 文件，返回键值映射。支持带引号值和 # 注释。"""
    result: dict[str, str] = {}
    if not path.is_file():
        return result
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        # 去除引号
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        result[key] = value
    return result


def load_auth(account: int = 1) -> TencentDocsAuth:
    """加载指定账号的认证信息。

    Args:
        account: 账号编号 (1 或 2)，默认 1。

    Returns:
        TencentDocsAuth 实例。

    Raises:
        ValueError: 账号编号无效或凭证缺失。
    """
    if account not in (1, 2):
        raise ValueError(f"账号编号必须为 1 或 2，收到: {account}")

    env_vars = _parse_env_file(_ENV_FILE)

    prefix = f"TENCENTDOCS{account}_"
    access_token = env_vars.get(f"{prefix}ACCESS_TOKEN", "")
    client_id = env_vars.get(f"{prefix}CLIENT_ID", "")
    open_id = env_vars.get(f"{prefix}OPEN_ID", "")

    # 回退到无前缀默认值（仅 account=1）
    if account == 1:
        if not access_token:
            access_token = env_vars.get("TENCENTDOCS_ACCESS_TOKEN", "")
        if not client_id:
            client_id = env_vars.get("TENCENTDOCS_CLIENT_ID", "")
        if not open_id:
            open_id = env_vars.get("TENCENTDOCS_OPEN_ID", "")

    # 最后回退到系统环境变量
    if not access_token:
        access_token = os.environ.get(f"{prefix}ACCESS_TOKEN", "")
    if not client_id:
        client_id = os.environ.get(f"{prefix}CLIENT_ID", "")
    if not open_id:
        open_id = os.environ.get(f"{prefix}OPEN_ID", "")

    if not access_token or not client_id or not open_id:
        missing = []
        if not access_token:
            missing.append(f"{prefix}ACCESS_TOKEN")
        if not client_id:
            missing.append(f"{prefix}CLIENT_ID")
        if not open_id:
            missing.append(f"{prefix}OPEN_ID")
        raise ValueError(f"凭证缺失: {', '.join(missing)}，请检查 .env 文件")

    return TencentDocsAuth(
        access_token=access_token,
        client_id=client_id,
        open_id=open_id,
    )


def get_base_url() -> str:
    """返回 API 基础 URL。"""
    return _BASE_URL
