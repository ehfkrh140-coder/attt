from __future__ import annotations


def diff_states(pre: dict[str, object], post: dict[str, object]) -> dict[str, tuple[object, object]]:
    keys = set(pre) | set(post)
    return {key: (pre.get(key), post.get(key)) for key in sorted(keys) if pre.get(key) != post.get(key)}
