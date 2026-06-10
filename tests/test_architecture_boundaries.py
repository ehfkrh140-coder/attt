from __future__ import annotations

from pathlib import Path

RED_BLUE_DIRS = [Path("redteam"), Path("blue")]
RAW_PROVIDER_PATTERNS = [
    "send_raw_transaction",
    "eth_sendRawTransaction",
    "account.sign_transaction",
    "sign_transaction",
    "Web3.HTTPProvider",
    "Web3.WebsocketProvider",
    "HTTPProvider",
    "WebsocketProvider",
    "w3.eth.send_transaction",
    "w3.eth.send_raw_transaction",
    "requests.post",
    "httpx.post",
    "aiohttp",
]
PUBLIC_RPC_PATTERNS = ["infura", "alchemy", "quicknode", "ankr", "blastapi", "publicnode"]


def source_text() -> str:
    chunks = []
    for directory in RED_BLUE_DIRS:
        for path in directory.rglob("*.py"):
            chunks.append(path.read_text())
    return "\n".join(chunks)


def test_red_blue_no_raw_provider_access():
    text = source_text()
    assert not any(pattern in text for pattern in RAW_PROVIDER_PATTERNS)


def test_red_blue_no_private_key_usage():
    assert "private_key" not in source_text()


def test_red_blue_no_public_rpc_strings():
    text = source_text().lower()
    assert "https://" not in text
    assert not any(pattern in text for pattern in PUBLIC_RPC_PATTERNS)
