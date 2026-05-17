# Auth App Starter

This starter demonstrates Aquilia auth with explicit identity and credential stores, access and refresh token issuance, a protected profile route, and an admin-only route. It keeps storage in memory so the code can run locally while still using `AuthManager`, `TokenManager`, guards, and framework identity types.

In production, replace the memory stores with durable stores and load token secrets from environment-backed configuration.
