import asyncio
import logging
import uuid as uuid_lib
from datetime import datetime
from app.db.session import SessionLocal
from app.models.scan import ScanJob, ScanResult, ScanStatus, RiskLevel
from app.scanner.runner import run_full_scan

logger = logging.getLogger(__name__)


def run_scan(scan_id: str):
    """RQ worker entry point. Runs the scan synchronously (wraps async)."""
    asyncio.run(_run_scan_async(scan_id))


async def _run_scan_async(scan_id: str):
    db = SessionLocal()
    try:
        try:
            uid = uuid_lib.UUID(scan_id)
        except ValueError:
            logger.error(f"Invalid scan_id format received by worker: {scan_id!r}")
            return

        scan = db.query(ScanJob).filter(ScanJob.id == uid).first()
        if not scan:
            logger.error(f"Scan {scan_id} not found")
            return

        scan.status = ScanStatus.running
        scan.progress = 10
        scan.updated_at = datetime.utcnow()
        db.commit()

        async def progress_callback(pct: int, msg: str = ""):
            s = db.query(ScanJob).filter(ScanJob.id == uid).first()
            if s:
                s.progress = pct
                s.updated_at = datetime.utcnow()
                db.commit()
            logger.info(f"[{scan_id}] {pct}% — {msg}")

        result = await run_full_scan(scan.url, progress_callback=progress_callback)

        # Save result
        scan_result = ScanResult(
            scan_id=scan.id,
            raw_html_snapshot=result.get("raw_html_snapshot"),
            pages_checked=result.get("pages_checked", []),
            checks=result.get("checks", []),
            issues=result.get("issues", []),
            recommendations=result.get("recommendations", []),
            meta=result.get("meta", {}),
        )
        db.add(scan_result)

        scan.status = ScanStatus.completed
        scan.progress = 100
        scan.score = result["score"]
        scan.risk_level = RiskLevel(result["risk_level"])
        scan.finished_at = datetime.utcnow()
        scan.updated_at = datetime.utcnow()
        db.commit()

        logger.info(f"Scan {scan_id} completed. Score: {result['score']}, Risk: {result['risk_level']}")

    except Exception as e:
        logger.exception(f"Scan {scan_id} failed: {e}")
        try:
            _uid = uuid_lib.UUID(scan_id) if isinstance(scan_id, str) else scan_id
            scan = db.query(ScanJob).filter(ScanJob.id == _uid).first()
            if scan:
                scan.status = ScanStatus.failed
                scan.error = str(e)[:1000]
                scan.finished_at = datetime.utcnow()
                scan.updated_at = datetime.utcnow()
                db.commit()
        except Exception as inner:
            logger.exception(f"Failed to update scan status: {inner}")
    finally:
        db.close()
