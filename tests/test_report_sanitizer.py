from __future__ import annotations

import pytest

from core.errors import SafetyGuardError
from core.safety import BLOCKED_BY_SAFETY_GUARD, SafetyGuard


def blocked(report: str) -> None:
    with pytest.raises(SafetyGuardError, match=BLOCKED_BY_SAFETY_GUARD):
        SafetyGuard().assert_safe_report(report)


def test_report_sanitizer_blocks_raw_calldata():
    blocked("raw_calldata: 0x1234567890abcdef1234")
    blocked("calldata: reusable transaction payload")
    blocked("payload 0x1234567890abcdef1234567890abcdef")


def test_report_sanitizer_blocks_private_key():
    blocked("private_key=secret")
    blocked("mnemonic words go here")
    blocked("seed phrase included")
    blocked("account.sign_transaction(...) snippet")


def test_report_sanitizer_blocks_public_rpc_url():
    blocked("https://mainnet.infura.io/v3/token")
    blocked("https://rpc.ankr.com/eth")
    blocked("curl -X POST https://rpc.example.invalid -d '{}' ")


def test_report_sanitizer_allows_safe_labels():
    safe = "safe:oracle-divergence-probe safe:defense-pause mock-only local-only arena-contained"
    assert SafetyGuard().assert_safe_report(safe).allowed
