from src.modules.health.schemas import HealthResponse

def get_health() -> HealthResponse:
    return HealthResponse(status="ok")
