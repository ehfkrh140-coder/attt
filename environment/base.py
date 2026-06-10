from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class EnvironmentEvent:
    component: str
    mode: str
    description: str
    local_only: bool = True
    visible_to_blue: bool = True
    details: dict[str, object] = field(default_factory=dict)

    def safe_dict(self) -> dict[str, object]:
        return {
            "component": self.component,
            "mode": self.mode,
            "description": self.description,
            "local_only": self.local_only,
            "visible_to_blue": self.visible_to_blue,
        }


class LocalOnlyTwinComponent:
    component_name = "base"

    def emit(self, mode: str) -> EnvironmentEvent:
        return EnvironmentEvent(self.component_name, mode, f"{self.component_name}:{mode}")
