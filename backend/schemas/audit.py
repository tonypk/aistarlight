from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: str
    tenant_id: str
    user_id: str | None
    entity_type: str
    entity_id: str | None
    action: str
    changes: dict | None
    comment: str | None
    created_at: str

    model_config = {"from_attributes": True}
