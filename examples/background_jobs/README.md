# Background Jobs Starter

This starter shows Aquilia tasks with on-demand dispatch, priority queues, retry settings, scheduled cleanup, and job status inspection. The controller starts the in-memory task manager lazily for local development.

For production, start the task manager during application startup and use a durable backend when jobs must survive process restarts.
