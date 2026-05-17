from aquilia.engine import get_engine_metrics


class OperationsService:
    async def health(self):
        return {"status": "ok", "service": "aquilia-native-commerce"}

    async def runtime_metrics(self):
        return get_engine_metrics().snapshot()

    async def readiness(self):
        return {
            "database": "configured",
            "tasks": "configured",
            "storage": "configured",
            "mail": "configured",
            "sockets": "configured",
        }
