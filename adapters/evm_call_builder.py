from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class EvmCall:
    safe_label: str
    selector: str
    encoded_args: tuple[str, ...] = field(default_factory=tuple)
    lookup_args: tuple[str, ...] = field(default_factory=tuple)

    @property
    def data(self) -> str:
        return self.selector + "".join(arg.removeprefix("0x") for arg in self.encoded_args)


class EvmCallBuilder:
    _CALLS: dict[str, str] = {
        "aave_provider_get_pool": "0x026b1d5f",
        "aave_provider_get_pool_configurator": "0x3d01de59",
        "aave_provider_get_price_oracle": "0x1f4691b4",
        "aave_provider_get_acl_manager": "0x997a1378",
        "aave_pool_get_reserves_list": "0xd1946dbc",
        "aave_pool_get_reserve_data": "0x35ea6a75",
    }

    @classmethod
    def build(cls, safe_label: str, *encoded_args: str, lookup_args: tuple[str, ...] = ()) -> EvmCall:
        if safe_label not in cls._CALLS:
            raise ValueError(f"Unsupported safe EVM read label: {safe_label}")
        return EvmCall(safe_label=safe_label, selector=cls._CALLS[safe_label], encoded_args=tuple(encoded_args), lookup_args=tuple(lookup_args))

    @classmethod
    def encode_address_arg(cls, address: str) -> str:
        if address.startswith("0x") and len(address) == 42:
            return "0x" + address.removeprefix("0x").lower().rjust(64, "0")
        return ""

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

    @classmethod
    def aave_pool_get_reserves_list(cls) -> EvmCall:
        return cls.build("aave_pool_get_reserves_list")

    @classmethod
    def aave_pool_get_reserve_data(cls, reserve_asset: str) -> EvmCall:
        return cls.build("aave_pool_get_reserve_data", cls.encode_address_arg(reserve_asset), lookup_args=(reserve_asset,))
