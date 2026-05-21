import uuid
import redis
from rq import Queue
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.db.session import get_db
from app.models.scan import ScanJob, ScanStatus
from app.schemas.scan import ScanCreateRequest, ScanCreateResponse, ScanJobResponse, CheckSchema, IssueSchema
from app.core.config import settings
from app.core.url_utils import normalize_url

router = APIRouter(prefix="/api/scans", tags=["scans"])
# Rate limit string is evaluated at import time from settings.
# To change the limit, update RATE_LIMIT_PER_MINUTE in .env and restart the service.
limiter = Limiter(key_func=get_remote_address)


def get_redis():
    return redis.from_url(settings.REDIS_URL)


def get_queue(r=None):
    if r is None:
        r = get_redis()
    return Queue("scans", connection=r)


@router.post("", response_model=ScanCreateResponse)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
def create_scan(payload: ScanCreateRequest, request: Request, db: Session = Depends(get_db)):
    normalized, err = normalize_url(payload.url)
    if err:
        raise HTTPException(status_code=422, detail=err)

    scan = ScanJob(
        id=uuid.uuid4(),
        url=payload.url,
        normalized_url=normalized,
        status=ScanStatus.queued,
        progress=0,
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)

    # Enqueue task
    r = get_redis()
    q = get_queue(r)
    q.enqueue(
        "app.workers.tasks.run_scan",
        str(scan.id),
        job_timeout=300,
    )

    return ScanCreateResponse(scan_id=str(scan.id), status="queued")


@router.get("/{scan_id}", response_model=ScanJobResponse)
def get_scan(scan_id: str, db: Session = Depends(get_db)):
    try:
        uid = uuid.UUID(scan_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Некорректный идентификатор сканирования")

    scan = db.query(ScanJob).filter(ScanJob.id == uid).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Сканирование не найдено")

    checks = []
    issues = []

    if scan.result:
        checks = [CheckSchema(**c) for c in (scan.result.checks or [])]
        issues = [IssueSchema(**i) for i in (scan.result.issues or [])]

    return ScanJobResponse(
        id=str(scan.id),
        url=scan.url,
        status=scan.status.value,
        progress=scan.progress,
        score=scan.score,
        risk_level=scan.risk_level.value if scan.risk_level else None,
        checks=checks,
        issues=issues,
        created_at=scan.created_at,
        finished_at=scan.finished_at,
        error=scan.error,
    )


@router.get("/{scan_id}/pdf")
async def get_scan_pdf(scan_id: str, db: Session = Depends(get_db)):
    try:
        uid = uuid.UUID(scan_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Некорректный идентификатор сканирования")

    scan = db.query(ScanJob).filter(ScanJob.id == uid).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Сканирование не найдено")

    if scan.status != ScanStatus.completed:
        raise HTTPException(status_code=400, detail="Сканирование ещё не завершено")

    if not scan.result:
        raise HTTPException(status_code=404, detail="Результаты сканирования не найдены")

    from app.pdf.generator import generate_pdf

    scan_data = {
        "url": scan.url,
        "score": scan.score,
        "risk_level": scan.risk_level.value if scan.risk_level else "red",
    }
    result_data = {
        "checks": scan.result.checks or [],
        "issues": scan.result.issues or [],
        "recommendations": scan.result.recommendations or [],
        "meta": scan.result.meta or {},
    }

    pdf_bytes = await generate_pdf(scan_data, result_data)

    safe_domain = scan.url.replace("https://", "").replace("http://", "").split("/")[0]
    filename = f"siteguard_{safe_domain}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
