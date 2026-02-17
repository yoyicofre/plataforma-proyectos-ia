from fastapi import FastAPI

from src.core.config import settings
from src.core.logging import configure_logging

# [agentops:routers-imports:start]
from src.modules.agent_catalog.router import router as agent_catalog_router
from src.modules.agent_runs.router import router as agent_runs_router
from src.modules.ai_providers.router import router as ai_providers_router
from src.modules.auth.router import router as auth_router
from src.modules.costs.router import router as costs_router
from src.modules.health.router import router as health_router
from src.modules.me_context.router import router as me_context_router
from src.modules.me_dashboard.router import router as me_dashboard_router
from src.modules.project_agent_assignments.router import (
    router as project_agent_assignments_router,
)
from src.modules.project_members.router import router as project_members_router
from src.modules.project_permissions.router import router as project_permissions_router
from src.modules.project_stage_status.router import router as project_stage_status_router
from src.modules.projects.router import router as projects_router
from src.modules.users.router import router as users_router
# [agentops:routers-imports:end]

configure_logging(settings.log_level)


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version="0.1.0")

    # [agentops:routers-include:start]
    app.include_router(agent_catalog_router, prefix="/agents", tags=["agent-catalog"])
    app.include_router(agent_runs_router, prefix="/agent-runs", tags=["agent-runs"])
    app.include_router(ai_providers_router, prefix="/ai", tags=["ai-providers"])
    app.include_router(auth_router, prefix="/auth", tags=["auth"])
    app.include_router(costs_router, prefix="/costs", tags=["costs"])
    app.include_router(health_router)
    app.include_router(me_context_router, tags=["me-context"])
    app.include_router(me_dashboard_router, tags=["me-dashboard"])
    app.include_router(
        project_agent_assignments_router,
        prefix="/project-agent-assignments",
        tags=["project-agent-assignments"],
    )
    app.include_router(project_members_router, tags=["project-members"])
    app.include_router(project_permissions_router, tags=["project-permissions"])
    app.include_router(project_stage_status_router, tags=["project-stage-status"])
    app.include_router(projects_router, prefix="/projects", tags=["projects"])
    app.include_router(users_router, prefix="/users", tags=["users"])
    # [agentops:routers-include:end]

    return app


app = create_app()
