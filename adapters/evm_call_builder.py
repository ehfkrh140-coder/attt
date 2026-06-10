from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EvmCall:
    safe_label: str
    selector: str


class EvmCallBuilder:
    _CALLS: dict[str, str] = {
        "aave_provider_get_pool": "0x026b1d5f",
        "aave_provider_get_pool_configurator": "0x3d01de59",
        "aave_provider_get_price_oracle": "0x1f4691b4",
        "aave_provider_get_acl_manager": "0x997a1378",
    }

    @classmethod
    def build(cls, safe_label: str) -> EvmCall:
        if safe_label not in cls._CALLS:
            raise ValueError(f"Unsupported safe EVM read label: {safe_label}")
        return EvmCall(safe_label=safe_label, selector=cls._CALLS[safe_label])

    @classmethod
    def aave_provider_get_pool(cls) -> EvmCall:
        return cls.build("aave_provider_get_pool")

    @classmethod
    def aave_provider_get_pool_configurator(cls) -> EvmCall:
        return cls.build("aave_provider_get_pool_configurator")

    @classmethod
    def aave_provider_get_price_oracle(cls) -> EvmCall:
        return cls.build("aave_provider_get_price_oracle")

    @classmethod
    def aave_provider_get_acl_manager(cls) -> EvmCall:
        return cls.build("aave_provider_get_acl_manager")
