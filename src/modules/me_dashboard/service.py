from datetime import UTC, datetime

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.core.security import User
from src.modules.me_dashboard.schemas import (
    MeDashboardKpisOut,
    MeDashboardOut,
    MeDashboardProjectOut,
)


def get_me_dashboard(db: Session, user: User, limit: int = 20) -> MeDashboardOut:
    user_id = int(user.id)

    projects_count = int(
        db.execute(
            text("SELECT COUNT(*) FROM project_members WHERE user_id = :user_id"),
            {"user_id": user_id},
        ).scalar_one()
    )

    blocked_stages_count = int(
        db.execute(
            text(
                """
                SELECT COUNT(*)
                FROM project_stage_status pss
                JOIN project_members pm ON pm.project_id = pss.project_id
                WHERE pm.user_id = :user_id
                  AND pss.stage_status = 'blocked'
                """
            ),
            {"user_id": user_id},
        ).scalar_one()
    )

    failed_runs_count_7d = int(
        db.execute(
            text(
                """
                SELECT COUNT(*)
                FROM agent_runs ar
                JOIN project_members pm ON pm.project_id = ar.project_id
                WHERE pm.user_id = :user_id
                  AND ar.run_status = 'failed'
                  AND ar.created_at >= UTC_TIMESTAMP() - INTERVAL 7 DAY
                """
            ),
            {"user_id": user_id},
        ).scalar_one()
    )

    queued_runs_count = int(
        db.execute(
            text(
                """
                SELECT COUNT(*)
                FROM agent_runs ar
                JOIN project_members pm ON pm.project_id = ar.project_id
                WHERE pm.user_id = :user_id
                  AND ar.run_status = 'queued'
                """
            ),
            {"user_id": user_id},
        ).scalar_one()
    )

    published_artifacts_count = int(
        db.execute(
            text(
                """
                SELECT COUNT(*)
                FROM project_artifacts pa
                JOIN project_members pm ON pm.project_id = pa.project_id
                WHERE pm.user_id = :user_id
                  AND pa.artifact_status = 'published'
                """
            ),
            {"user_id": user_id},
        ).scalar_one()
    )

    cost_usd_total_30d = float(
        db.execute(
            text(
                """
                SELECT COALESCE(SUM(ar.cost_usd), 0)
                FROM agent_runs ar
                JOIN project_members pm ON pm.project_id = ar.project_id
                WHERE pm.user_id = :user_id
                  AND ar.created_at >= UTC_TIMESTAMP() - INTERVAL 30 DAY
                """
            ),
            {"user_id": user_id},
        ).scalar_one()
    )

    project_rows = (
        db.execute(
            text(
                """
                SELECT
                  p.project_id,
                  p.project_key,
                  p.project_name,
                  p.lifecycle_status,
                  p.updated_at,
                  pm.member_role,
                  COALESCE(bs.blocked_stages_count, 0) AS blocked_stages_count,
                  COALESCE(fr.failed_runs_count_7d, 0) AS failed_runs_count_7d,
                  COALESCE(qr.queued_runs_count, 0) AS queued_runs_count,
                  COALESCE(cst.cost_usd_total_30d, 0) AS cost_usd_total_30d
                FROM projects p
                JOIN project_members pm ON pm.project_id = p.project_id
                LEFT JOIN (
                  SELECT project_id, COUNT(*) AS blocked_stages_count
                  FROM project_stage_status
                  WHERE stage_status = 'blocked'
                  GROUP BY project_id
                ) bs ON bs.project_id = p.project_id
                LEFT JOIN (
                  SELECT project_id, COUNT(*) AS failed_runs_count_7d
                  FROM agent_runs
                  WHERE run_status = 'failed'
                    AND created_at >= UTC_TIMESTAMP() - INTERVAL 7 DAY
                  GROUP BY project_id
                ) fr ON fr.project_id = p.project_id
                LEFT JOIN (
                  SELECT project_id, COUNT(*) AS queued_runs_count
                  FROM agent_runs
                  WHERE run_status = 'queued'
                  GROUP BY project_id
                ) qr ON qr.project_id = p.project_id
                LEFT JOIN (
                  SELECT project_id, COALESCE(SUM(cost_usd), 0) AS cost_usd_total_30d
                  FROM agent_runs
                  WHERE created_at >= UTC_TIMESTAMP() - INTERVAL 30 DAY
                  GROUP BY project_id
                ) cst ON cst.project_id = p.project_id
                WHERE pm.user_id = :user_id
                ORDER BY p.updated_at DESC, p.project_id DESC
                LIMIT :limit
                """
            ),
            {"user_id": user_id, "limit": limit},
        )
        .mappings()
        .all()
    )

    projects = [MeDashboardProjectOut(**dict(row)) for row in project_rows]
    return MeDashboardOut(
        user_id=user_id,
        generated_at=datetime.now(UTC),
        kpis=MeDashboardKpisOut(
            projects_count=projects_count,
            blocked_stages_count=blocked_stages_count,
            failed_runs_count_7d=failed_runs_count_7d,
            queued_runs_count=queued_runs_count,
            published_artifacts_count=published_artifacts_count,
            cost_usd_total_30d=cost_usd_total_30d,
        ),
        projects=projects,
    )
