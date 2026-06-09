from __future__ import annotations


def decode_safe_features(pending_features: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "target": item.get("target"),
            "function_category": item.get("function_category"),
            "calldata_label": item.get("calldata_label"),
            "sender_role": item.get("sender_role"),
            "value": item.get("value", 0),
        }
        for item in pending_features
    ]
