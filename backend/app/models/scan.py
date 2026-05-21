import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.session import Base


class ScanStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class RiskLevel(str, enum.Enum):
    green = "green"
    yellow = "yellow"
    red = "red"


class ScanJob(Base):
    __tablename__ = "scan_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url = Column(String(2048), nullable=False)
    normalized_url = Column(String(2048), nullable=False)
    status = Column(SAEnum(ScanStatus), nullable=False, default=ScanStatus.queued)
    progress = Column(Integer, nullable=False, default=0)
    score = Column(Integer, nullable=True)
    risk_level = Column(SAEnum(RiskLevel), nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)

    result = relationship("ScanResult", back_populates="scan", uselist=False)


class ScanResult(Base):
    __tablename__ = "scan_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_id = Column(UUID(as_uuid=True), ForeignKey("scan_jobs.id", ondelete="CASCADE"), nullable=False)
    raw_html_snapshot = Column(Text, nullable=True)
    pages_checked = Column(JSONB, nullable=True, default=list)
    checks = Column(JSONB, nullable=True, default=list)
    issues = Column(JSONB, nullable=True, default=list)
    recommendations = Column(JSONB, nullable=True, default=list)
    meta = Column(JSONB, nullable=True, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    scan = relationship("ScanJob", back_populates="result")
