# WebSocket App Starter

This starter provides a chat namespace with connection hooks, room subscription, acknowledgements, presence, and a small HTTP controller for room inspection. It uses the Aquilia socket decorators and connection API directly.

The room registry is in memory for local development. Use the Redis socket adapter when you need fanout across multiple workers.
