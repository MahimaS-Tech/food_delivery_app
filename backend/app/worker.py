from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

from sqlalchemy import select

from app.core.database import configure_database, create_schema, session_scope
from app.models.enums import OutboxStatus
from app.models.outbox import OutboxEvent

logger = logging.getLogger("food-delivery-worker")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def publish_event(event: OutboxEvent) -> None:
    """Placeholder publisher.

    Replace this with Kafka/SNS/SQS/RabbitMQ publishing in production. Keeping it
    deterministic in this starter makes tests and local Docker runs simple.
    """
    logger.info("publishing event id=%s type=%s payload=%s", event.id, event.event_type, event.payload_json)


def process_pending_events(batch_size: int = 50) -> int:
    processed = 0
    with session_scope() as db:
        events = list(
            db.scalars(
                select(OutboxEvent)
                .where(OutboxEvent.status == OutboxStatus.PENDING.value)
                .order_by(OutboxEvent.created_at.asc())
                .limit(batch_size)
            ).all()
        )
        for event in events:
            try:
                publish_event(event)
                event.status = OutboxStatus.PUBLISHED.value
                event.published_at = datetime.now(timezone.utc)
            except Exception:
                logger.exception("failed to publish outbox event %s", event.id)
                event.retry_count += 1
                if event.retry_count >= 5:
                    event.status = OutboxStatus.FAILED.value
            processed += 1
    return processed


def main() -> None:
    configure_database()
    create_schema()
    while True:
        processed = process_pending_events()
        if processed == 0:
            time.sleep(2)


if __name__ == "__main__":
    main()
