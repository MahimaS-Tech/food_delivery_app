from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.models.outbox import OutboxEvent


def add_outbox_event(db: Session, aggregate_type: str, aggregate_id: str, event_type: str, payload: dict) -> OutboxEvent:
    event = OutboxEvent(
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        event_type=event_type,
        payload_json=json.dumps(payload, sort_keys=True),
    )
    db.add(event)
    return event
