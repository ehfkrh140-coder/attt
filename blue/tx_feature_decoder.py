from __future__ import annotations

from redteam.executable_drill import BLIND_FEATURE_KEYS, BlindTxFeature


def decode_safe_features(pending_features: list[BlindTxFeature | dict[str, object]]) -> list[dict[str, object]]:
    decoded: list[dict[str, object]] = []
    for item in pending_features:
        feature = item.to_dict() if isinstance(item, BlindTxFeature) else dict(item)
        decoded.append({key: feature.get(key) for key in BLIND_FEATURE_KEYS})
    return decoded
