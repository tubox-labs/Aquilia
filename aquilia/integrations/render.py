"""
RenderIntegration — typed Render PaaS deployment configuration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class RenderIntegration:
    """
    Typed Render deployment configuration.

    Example::

        RenderIntegration(
            region="frankfurt",
            plan="standard",
            num_instances=2,
        )
    """

    _integration_type: str = field(default="render", init=False, repr=False)

    service_name: Optional[str] = None
    region: str = "oregon"
    plan: str = "starter"
    num_instances: int = 1
    image: Optional[str] = None
    health_path: str = "/_health"
    auto_deploy: str = "no"
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        config: Dict[str, Any] = {
            "_integration_type": "render",
            "enabled": self.enabled,
            "region": self.region,
            "plan": self.plan,
            "num_instances": self.num_instances,
            "health_path": self.health_path,
            "auto_deploy": self.auto_deploy,
        }
        if self.service_name:
            config["service_name"] = self.service_name
        if self.image:
            config["image"] = self.image
        return config
