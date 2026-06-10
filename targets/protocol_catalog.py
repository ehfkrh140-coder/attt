from __future__ import annotations

from dataclasses import dataclass

UNSUPPORTED_PROTOCOL_TWIN = "UNSUPPORTED_PROTOCOL_TWIN"
MISSING_PROTOCOL_ROOT_ADDRESS = "MISSING_PROTOCOL_ROOT_ADDRESS"
UNSUPPORTED_ENVIRONMENT_TWIN_COMPONENT = "UNSUPPORTED_ENVIRONMENT_TWIN_COMPONENT"


@dataclass(frozen=True)
class ProtocolCatalogEntry:
    protocol: str
    runtime: str
    twin_mode: str
    status: str
    known_roots: dict[str, str]


class ProtocolCatalog:
    def __init__(self) -> None:
        self._entries = {
            "mock_lending": ProtocolCatalogEntry(
                protocol="mock_lending",
                runtime="mock",
                twin_mode="mockarena",
                status="supported_mock_only",
                known_roots={},
            ),
            "aave_v3": ProtocolCatalogEntry(
                protocol="aave_v3",
                runtime="evm",
                twin_mode="evm_fork_twin",
                status="supported_readonly_or_gated_execution",
                known_roots={},
            ),
            "haedal": ProtocolCatalogEntry(
                protocol="haedal",
                runtime="sui_move",
                twin_mode="sui_state_twin",
                status="gated_unsupported_until_sui_adapter",
                known_roots={},
            ),
        }

    def get(self, protocol: str) -> ProtocolCatalogEntry:
        key = protocol.lower()
        if key not in self._entries:
            raise KeyError(protocol)
        return self._entries[key]

    def all(self) -> dict[str, ProtocolCatalogEntry]:
        return dict(self._entries)
