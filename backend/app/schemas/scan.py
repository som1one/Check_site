from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, field_validator


class ScanCreateRequest(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        v = v.strip()
        if not v.startswith(("http://", "https://")):
            v = "https://" + v
        return v


class ScanCreateResponse(BaseModel):
    scan_id: str
    status: str


class IssueSchema(BaseModel):
    code: str
    title: str
    severity: str  # high | medium | low
    category: str  # personal_data | cookies | ads | company_info | consumer_rights | technical
    description: str
    recommendation: str
    evidence: List[str] = []
    possible_fine: Optional[int] = None


class CheckSchema(BaseModel):
    code: str
    title: str
    status: str  # passed | warning | failed
    details: str
    evidence: List[str] = []


class ScanJobResponse(BaseModel):
    id: str
    url: str
    status: str
    progress: int
    score: Optional[int] = None
    risk_level: Optional[str] = None
    checks: List[CheckSchema] = []
    issues: List[IssueSchema] = []
    created_at: datetime
    finished_at: Optional[datetime] = None
    error: Optional[str] = None

    class Config:
        from_attributes = True
