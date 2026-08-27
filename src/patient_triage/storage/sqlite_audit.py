"""Append-only, hash-chained SQLite audit storage."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from typing import Any
from uuid import uuid4

from patient_triage.domain.audit import AuditEvent


class SQLiteAuditStore:
    def __init__(self, database_path: Path | str) -> None:
        self.path = Path(database_path)
        if self.path != Path(":memory:"):
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(str(self.path), check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._lock = RLock()
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.execute("PRAGMA journal_mode = WAL")
        self._create_schema()

    def _create_schema(self) -> None:
        with self._connection:
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_events (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL UNIQUE,
                    occurred_at TEXT NOT NULL,
                    actor_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    patient_id TEXT,
                    payload_json TEXT NOT NULL,
                    model_version TEXT NOT NULL,
                    previous_hash TEXT NOT NULL,
                    event_hash TEXT NOT NULL UNIQUE
                )
                """
            )

    @staticmethod
    def _hash_event(
        event_id: str,
        occurred_at: str,
        actor_id: str,
        event_type: str,
        patient_id: str | None,
        payload_json: str,
        model_version: str,
        previous_hash: str,
    ) -> str:
        canonical = "|".join(
            (
                previous_hash,
                event_id,
                occurred_at,
                actor_id,
                event_type,
                patient_id or "",
                payload_json,
                model_version,
            )
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def append(
        self,
        *,
        actor_id: str,
        event_type: str,
        payload: dict[str, Any],
        model_version: str,
        patient_id: str | None = None,
        occurred_at: datetime | None = None,
    ) -> AuditEvent:
        timestamp = occurred_at or datetime.now(UTC)
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError("audit timestamp must include a timezone")
        timestamp_text = timestamp.isoformat()
        event_id = str(uuid4())
        payload_json = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), default=str
        )

        with self._lock, self._connection:
            row = self._connection.execute(
                "SELECT event_hash FROM audit_events ORDER BY sequence DESC LIMIT 1"
            ).fetchone()
            previous_hash = row["event_hash"] if row else "GENESIS"
            event_hash = self._hash_event(
                event_id,
                timestamp_text,
                actor_id,
                event_type,
                patient_id,
                payload_json,
                model_version,
                previous_hash,
            )
            self._connection.execute(
                """
                INSERT INTO audit_events (
                    event_id, occurred_at, actor_id, event_type, patient_id,
                    payload_json, model_version, previous_hash, event_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    timestamp_text,
                    actor_id,
                    event_type,
                    patient_id,
                    payload_json,
                    model_version,
                    previous_hash,
                    event_hash,
                ),
            )
        return AuditEvent(
            event_id=event_id,
            occurred_at=timestamp,
            actor_id=actor_id,
            event_type=event_type,
            patient_id=patient_id,
            payload=json.loads(payload_json),
            model_version=model_version,
            previous_hash=previous_hash,
            event_hash=event_hash,
        )

    def list_events(self, limit: int = 100) -> list[AuditEvent]:
        if not 1 <= limit <= 1000:
            raise ValueError("audit limit must be between 1 and 1000")
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT * FROM audit_events
                ORDER BY sequence DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            AuditEvent(
                event_id=row["event_id"],
                occurred_at=datetime.fromisoformat(row["occurred_at"]),
                actor_id=row["actor_id"],
                event_type=row["event_type"],
                patient_id=row["patient_id"],
                payload=json.loads(row["payload_json"]),
                model_version=row["model_version"],
                previous_hash=row["previous_hash"],
                event_hash=row["event_hash"],
            )
            for row in rows
        ]

    def verify_chain(self) -> bool:
        with self._lock:
            rows = self._connection.execute(
                "SELECT * FROM audit_events ORDER BY sequence ASC"
            ).fetchall()
        expected_previous = "GENESIS"
        for row in rows:
            if row["previous_hash"] != expected_previous:
                return False
            calculated = self._hash_event(
                row["event_id"],
                row["occurred_at"],
                row["actor_id"],
                row["event_type"],
                row["patient_id"],
                row["payload_json"],
                row["model_version"],
                row["previous_hash"],
            )
            if calculated != row["event_hash"]:
                return False
            expected_previous = row["event_hash"]
        return True

    def close(self) -> None:
        with self._lock:
            self._connection.close()
