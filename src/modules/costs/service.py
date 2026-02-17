from sqlalchemy import text
from sqlalchemy.orm import Session

from src.core.security import User
from src.modules.costs.schemas import (
    CostByModelOut,
    CostByProjectOut,
    CostByProviderOut,
    CostSummaryOut,
)


def get_cost_summary(
    db: Session,
    user: User,
    days: int = 30,
    project_id: int | None = None,
) -> CostSummaryOut:
    base_params: dict[str, object] = {"user_id": int(user.id), "days": days, "project_id": project_id}

    total_row = (
        db.execute(
            text(
                """
                SELECT
                  COALESCE(SUM(ar.cost_usd), 0) AS total_cost_usd,
                  COUNT(*) AS total_runs_count
                FROM agent_runs ar
                JOIN project_members pm ON pm.project_id = ar.project_id
                WHERE pm.user_id = :user_id
                  AND ar.created_at >= UTC_TIMESTAMP() - INTERVAL :days DAY
                  AND (:project_id IS NULL OR ar.project_id = :project_id)
                """
            ),
            base_params,
        )
        .mappings()
        .first()
    )

    by_provider_rows = (
        db.execute(
            text(
                """
                SELECT
                  COALESCE(ar.provider, 'unknown') AS provider,
                  COALESCE(SUM(ar.cost_usd), 0) AS total_cost_usd,
                  COUNT(*) AS runs_count
                FROM agent_runs ar
                JOIN project_members pm ON pm.project_id = ar.project_id
                WHERE pm.user_id = :user_id
                  AND ar.created_at >= UTC_TIMESTAMP() - INTERVAL :days DAY
                  AND (:project_id IS NULL OR ar.project_id = :project_id)
                GROUP BY COALESCE(ar.provider, 'unknown')
                ORDER BY total_cost_usd DESC
                """
            ),
            base_params,
        )
        .mappings()
        .all()
    )

    by_model_rows = (
        db.execute(
            text(
                """
                SELECT
                  ar.provider,
                  ar.model_name,
                  COALESCE(SUM(ar.cost_usd), 0) AS total_cost_usd,
                  COUNT(*) AS runs_count
                FROM agent_runs ar
                JOIN project_members pm ON pm.project_id = ar.project_id
                WHERE pm.user_id = :user_id
                  AND ar.created_at >= UTC_TIMESTAMP() - INTERVAL :days DAY
                  AND (:project_id IS NULL OR ar.project_id = :project_id)
                GROUP BY ar.provider, ar.model_name
                ORDER BY total_cost_usd DESC
                """
            ),
            base_params,
        )
        .mappings()
        .all()
    )

    by_project_rows = (
        db.execute(
            text(
                """
                SELECT
                  p.project_id,
                  p.project_key,
                  p.project_name,
                  COALESCE(SUM(ar.cost_usd), 0) AS total_cost_usd,
                  COUNT(*) AS runs_count
                FROM projects p
                JOIN project_members pm ON pm.project_id = p.project_id
                JOIN agent_runs ar ON ar.project_id = p.project_id
                WHERE pm.user_id = :user_id
                  AND ar.created_at >= UTC_TIMESTAMP() - INTERVAL :days DAY
                  AND (:project_id IS NULL OR ar.project_id = :project_id)
                GROUP BY p.project_id, p.project_key, p.project_name
                ORDER BY total_cost_usd DESC
                """
            ),
            base_params,
        )
        .mappings()
        .all()
    )

    return CostSummaryOut(
        days=days,
        project_id=project_id,
        total_cost_usd=float((total_row or {}).get("total_cost_usd") or 0),
        total_runs_count=int((total_row or {}).get("total_runs_count") or 0),
        by_provider=[CostByProviderOut(**dict(row)) for row in by_provider_rows],
        by_model=[CostByModelOut(**dict(row)) for row in by_model_rows],
        by_project=[CostByProjectOut(**dict(row)) for row in by_project_rows],
    )
