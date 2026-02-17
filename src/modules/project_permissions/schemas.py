from pydantic import BaseModel


class ProjectPermissionsMeOut(BaseModel):
    project_id: int
    user_id: int
    member_role: str
    can_view_project: bool
    can_edit_project: bool
    can_view_members: bool
    can_manage_members: bool
    can_manage_stage_status: bool
    can_manage_assignments: bool
    can_create_agent_runs: bool
