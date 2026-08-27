from __future__ import annotations

from datetime import datetime

import pytest

from patient_triage.storage.sqlite_audit import SQLiteAuditStore


def test_audit_genesis_and_chain(now):
    store = SQLiteAuditStore(":memory:")
    try:
        first = store.append(
            actor_id="system",
            event_type="first",
            payload={"value": 1},
            model_version="test",
            occurred_at=now,
        )
        second = store.append(
            actor_id="nurse_01",
            event_type="second",
            patient_id="SYN-A",
            payload={"value": 2},
            model_version="test",
            occurred_at=now,
        )
        assert first.previous_hash == "GENESIS"
        assert second.previous_hash == first.event_hash
        assert store.verify_chain()
    finally:
        store.close()


def test_events_are_listed_newest_first(now):
    store = SQLiteAuditStore(":memory:")
    try:
        store.append(
            actor_id="a",
            event_type="one",
            payload={},
            model_version="v",
            occurred_at=now,
        )
        store.append(
            actor_id="a",
            event_type="two",
            payload={},
            model_version="v",
            occurred_at=now,
        )
        assert [event.event_type for event in store.list_events()] == ["two", "one"]
        assert len(store.list_events(limit=1)) == 1
    finally:
        store.close()


@pytest.mark.parametrize("limit", [0, 1001])
def test_invalid_audit_limit(limit):
    store = SQLiteAuditStore(":memory:")
    try:
        with pytest.raises(ValueError, match="between"):
            store.list_events(limit)
    finally:
        store.close()


def test_naive_audit_timestamp_rejected():
    store = SQLiteAuditStore(":memory:")
    try:
        with pytest.raises(ValueError, match="timezone"):
            store.append(
                actor_id="a",
                event_type="bad",
                payload={},
                model_version="v",
                occurred_at=datetime(2026, 1, 1),
            )
    finally:
        store.close()


def test_payload_tampering_breaks_chain(now):
    store = SQLiteAuditStore(":memory:")
    try:
        store.append(
            actor_id="a",
            event_type="one",
            payload={"x": 1},
            model_version="v",
            occurred_at=now,
        )
        store._connection.execute(
            "UPDATE audit_events SET payload_json = ? WHERE sequence = 1",
            ('{"x":999}',),
        )
        store._connection.commit()
        assert not store.verify_chain()
    finally:
        store.close()


def test_previous_hash_tampering_breaks_chain(now):
    store = SQLiteAuditStore(":memory:")
    try:
        store.append(
            actor_id="a",
            event_type="one",
            payload={},
            model_version="v",
            occurred_at=now,
        )
        store.append(
            actor_id="a",
            event_type="two",
            payload={},
            model_version="v",
            occurred_at=now,
        )
        store._connection.execute(
            "UPDATE audit_events SET previous_hash = 'wrong' WHERE sequence = 2"
        )
        store._connection.commit()
        assert not store.verify_chain()
    finally:
        store.close()
