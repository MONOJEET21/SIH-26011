from pydantic import BaseModel


class ValidationIssueCreate(BaseModel):
    entity_type: str
    entity_id: int
    issue_type: str
    message: str
    severity: str
    geometry: dict | None = None


class ValidationIssueResponse(BaseModel):
    id: int
    entity_type: str
    entity_id: int
    issue_type: str
    message: str
    severity: str
    status: str
    geometry: dict | None = None