import logging
import redis
from rq import Worker, Queue, Connection
from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


def main():
    conn = redis.from_url(settings.REDIS_URL)
    queues = [Queue("scans", connection=conn), Queue("default", connection=conn)]
    logger.info("Starting RQ worker, listening on queues: scans, default")
    with Connection(conn):
        worker = Worker(queues, connection=conn)
        worker.work(with_scheduler=True)


if __name__ == "__main__":
    main()
