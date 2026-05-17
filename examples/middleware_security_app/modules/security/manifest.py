from aquilia.manifest import AppManifest

manifest = AppManifest(
    name="security",
    version="1.0.0",
    description="Security policy module using middleware rate-limit rules and CSP policy primitives.",
    controllers=["modules.security.controllers:SecurityController"],
    services=["modules.security.services:SecurityPolicyService"],
    exports=["modules.security.services:SecurityPolicyService"],
    tags=["middleware", "security"],
)
