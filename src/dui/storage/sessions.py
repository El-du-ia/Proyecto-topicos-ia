"""
Sesiones persistentes en SQLite.

Un solo archivo (<datos>/dui.db) guarda las conversaciones COMPLETAS (incluidas
las llamadas a herramientas y sus resultados, para que al reanudar el agente
recuerde lo que encontró), la auditoría y un índice de búsqueda de texto (FTS5).

Se usa sqlite3 de la biblioteca estándar: funciona igual en Windows, Linux y macOS.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id            TEXT PRIMARY KEY,
    title         TEXT NOT NULL DEFAULT '',
    model         TEXT NOT NULL DEFAULT '',
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL,
    message_count INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS messages (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    seq        INTEGER NOT NULL,
    role       TEXT NOT NULL,
    content    TEXT NOT NULL DEFAULT '',
    payload    TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (session_id, seq)
);
CREATE TABLE IF NOT EXISTS audit (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    timestamp  TEXT NOT NULL,
    event      TEXT NOT NULL,
    data       TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, seq);
CREATE INDEX IF NOT EXISTS idx_audit_session ON audit(session_id, id);
"""

FTS_SCHEMA = """
CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
    content, content='messages', content_rowid='id', tokenize='unicode61 remove_diacritics 2'
);
CREATE TRIGGER IF NOT EXISTS messages_ai AFTER INSERT ON messages BEGIN
    INSERT INTO messages_fts(rowid, content) VALUES (new.id, new.content);
END;
CREATE TRIGGER IF NOT EXISTS messages_ad AFTER DELETE ON messages BEGIN
    INSERT INTO messages_fts(messages_fts, rowid, content) VALUES ('delete', old.id, old.content);
END;
"""


def new_session_id() -> str:
    """ID ordenable por fecha y fácil de citar por sus últimos 6 caracteres: 20261016_210137_47437b."""
    return f"{datetime.now():%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:6]}"


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _title_from(text: str, limit: int = 60) -> str:
    title = " ".join(text.split())
    return title if len(title) <= limit else title[: limit - 1].rstrip() + "…"


@dataclass(frozen=True)
class Session:
    id: str
    title: str
    model: str
    created_at: str
    updated_at: str
    message_count: int

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> Session:
        return cls(
            row["id"],
            row["title"],
            row["model"],
            row["created_at"],
            row["updated_at"],
            row["message_count"],
        )


@dataclass(frozen=True)
class SearchHit:
    session: Session
    snippet: str


class SessionNotFound(LookupError):
    pass


class SessionStore:
    def __init__(self, path: Path | str) -> None:
        """`path` puede ser ':memory:' para pruebas."""
        if str(path) != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self._conn = sqlite3.connect(str(path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.execute(
            "PRAGMA journal_mode = WAL" if str(path) != ":memory:" else "PRAGMA journal_mode = MEMORY"
        )
        self.has_fts = True
        self._migrate()

    def _migrate(self) -> None:
        with self._tx() as conn:
            conn.executescript(SCHEMA)
            try:
                conn.executescript(FTS_SCHEMA)
            except sqlite3.OperationalError:  # SQLite compilado sin FTS5: búsqueda con LIKE
                self.has_fts = False
            conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

    @contextmanager
    def _tx(self) -> Iterator[sqlite3.Connection]:
        try:
            yield self._conn
            self._conn.commit()
        except BaseException:
            self._conn.rollback()
            raise

    def close(self) -> None:
        self._conn.close()

    # ---------------------------------------------------------------- sesiones

    def create(self, session_id: str, model: str = "") -> Session:
        now = _now()
        with self._tx() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO sessions (id, model, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (session_id, model, now, now),
            )
        return self.get(session_id)

    def get(self, session_id: str) -> Session:
        row = self._conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        if row is None:
            raise SessionNotFound(session_id)
        return Session.from_row(row)

    def find(self, ref: str) -> Session:
        """Busca por ID completo o por un fragmento único del ID (p. ej. los últimos 6 caracteres)."""
        ref = ref.strip()
        try:
            return self.get(ref)
        except SessionNotFound:
            pass
        escaped = ref.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        rows = self._conn.execute(
            "SELECT * FROM sessions WHERE id LIKE ? ESCAPE '\\' AND message_count > 0 LIMIT 2",
            (f"%{escaped}%",),
        ).fetchall()
        if len(rows) == 1:
            return Session.from_row(rows[0])
        if not rows:
            raise SessionNotFound(f"No existe ninguna sesión '{ref}'.")
        raise SessionNotFound(f"'{ref}' coincide con varias sesiones; usa más caracteres del ID.")

    def list(self, limit: int = 20) -> list[Session]:
        rows = self._conn.execute(
            "SELECT * FROM sessions WHERE message_count > 0 ORDER BY updated_at DESC, id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [Session.from_row(r) for r in rows]

    def latest(self, exclude: str | None = None) -> Session | None:
        row = self._conn.execute(
            "SELECT * FROM sessions WHERE message_count > 0 AND id != ? "
            "ORDER BY updated_at DESC, id DESC LIMIT 1",
            (exclude or "",),
        ).fetchone()
        return Session.from_row(row) if row else None

    def rename(self, session_id: str, title: str) -> None:
        with self._tx() as conn:
            conn.execute("UPDATE sessions SET title = ? WHERE id = ?", (_title_from(title, 120), session_id))

    def delete(self, session_id: str) -> None:
        with self._tx() as conn:
            conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))

    def delete_empty(self) -> None:
        """Quita sesiones que se crearon pero nunca guardaron mensajes (ni auditoría)."""
        with self._tx() as conn:
            conn.execute(
                "DELETE FROM sessions WHERE message_count = 0 "
                "AND NOT EXISTS (SELECT 1 FROM audit WHERE audit.session_id = sessions.id)"
            )

    # ---------------------------------------------------------------- mensajes

    def append_messages(self, session_id: str, messages: list[dict[str, Any]], model: str = "") -> None:
        """Guarda mensajes nuevos de forma atómica (todo el turno o nada)."""
        if not messages:
            return
        now = _now()
        with self._tx() as conn:
            row = conn.execute(
                "SELECT title, message_count FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
            if row is None:
                raise SessionNotFound(session_id)
            seq = row["message_count"]
            for message in messages:
                content = message.get("content") or ""
                conn.execute(
                    "INSERT INTO messages (session_id, seq, role, content, payload, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        session_id,
                        seq,
                        message.get("role", ""),
                        content if isinstance(content, str) else json.dumps(content, ensure_ascii=False),
                        json.dumps(message, ensure_ascii=False, default=str),
                        now,
                    ),
                )
                seq += 1
            title = row["title"]
            if not title:
                first_user = next((m for m in messages if m.get("role") == "user" and m.get("content")), None)
                if first_user:
                    title = _title_from(str(first_user["content"]))
            conn.execute(
                "UPDATE sessions SET message_count = ?, updated_at = ?, title = ?, "
                "model = CASE WHEN ? != '' THEN ? ELSE model END WHERE id = ?",
                (seq, now, title, model, model, session_id),
            )

    def load_messages(self, session_id: str) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT payload FROM messages WHERE session_id = ? ORDER BY seq", (session_id,)
        ).fetchall()
        return [json.loads(r["payload"]) for r in rows]

    # ---------------------------------------------------------------- búsqueda

    def search(self, query: str, limit: int = 10) -> list[SearchHit]:
        query = query.strip()
        if not query:
            return []
        if self.has_fts:
            # Cada palabra como término literal (evita errores de sintaxis de FTS5 con comillas, guiones...).
            terms = " ".join('"' + word.replace('"', '""') + '"' for word in query.split())
            rows = self._conn.execute(
                "SELECT s.*, snippet(messages_fts, 0, '«', '»', '…', 12) AS snip "
                "FROM messages_fts JOIN messages m ON m.id = messages_fts.rowid "
                "JOIN sessions s ON s.id = m.session_id "
                "WHERE messages_fts MATCH ? ORDER BY rank LIMIT 200",
                (terms,),
            ).fetchall()
        else:
            escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            rows = self._conn.execute(
                "SELECT s.*, substr(m.content, 1, 80) AS snip FROM messages m "
                "JOIN sessions s ON s.id = m.session_id "
                "WHERE m.content LIKE ? ESCAPE '\\' ORDER BY s.updated_at DESC LIMIT 200",
                (f"%{escaped}%",),
            ).fetchall()
        hits: dict[str, SearchHit] = {}
        for row in rows:  # una coincidencia (la mejor) por sesión
            if row["id"] not in hits:
                hits[row["id"]] = SearchHit(Session.from_row(row), " ".join(row["snip"].split()))
            if len(hits) >= limit:
                break
        return list(hits.values())

    # ---------------------------------------------------------------- auditoría

    def record_audit(self, session_id: str, event: str, data: dict[str, Any], timestamp: str) -> None:
        with self._tx() as conn:
            conn.execute(
                "INSERT INTO audit (session_id, timestamp, event, data) VALUES (?, ?, ?, ?)",
                (session_id, timestamp, event, json.dumps(data, ensure_ascii=False, default=str)),
            )

    def audit_events(self, session_id: str) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT timestamp, event, data FROM audit WHERE session_id = ? ORDER BY id", (session_id,)
        ).fetchall()
        return [
            {
                "timestamp": r["timestamp"],
                "session_id": session_id,
                "event": r["event"],
                **json.loads(r["data"]),
            }
            for r in rows
        ]

    # ---------------------------------------------------------------- exportar

    def export_json(self, session_id: str) -> str:
        session = self.get(session_id)
        data = {
            "session": session.__dict__,
            "messages": self.load_messages(session_id),
            "audit": self.audit_events(session_id),
        }
        return json.dumps(data, ensure_ascii=False, indent=2, default=str)

    def export_markdown(self, session_id: str) -> str:
        session = self.get(session_id)
        lines = [
            f"# {session.title or 'Sesión ' + session.id}",
            "",
            f"- **Sesión:** `{session.id}`",
            f"- **Modelo:** {session.model or 'desconocido'}",
            f"- **Inicio:** {session.created_at} · **Última actividad:** {session.updated_at}",
            "",
            "## Conversación",
            "",
        ]
        for message in self.load_messages(session_id):
            role = message.get("role")
            content = (message.get("content") or "").strip()
            if role == "user":
                lines += [f"### 👤 Usuario\n\n{content}", ""]
            elif role == "assistant":
                for call in message.get("tool_calls") or []:
                    fn = call.get("function", {})
                    lines += [f"> 🔧 Herramienta `{fn.get('name')}` · argumentos `{fn.get('arguments')}`", ""]
                if content:
                    lines += [f"### 🤖 dui-IA\n\n{content}", ""]
            elif role == "tool":
                fence = "```"
                while fence in content:
                    fence += "`"
                lines += [
                    f"<details><summary>Resultado de {message.get('name')}</summary>\n",
                    f"{fence}text",
                    content,
                    fence,
                    "</details>",
                    "",
                ]
        events = self.audit_events(session_id)
        if events:
            lines += ["## Auditoría", "", "| Hora | Evento | Herramienta | Detalle |", "|---|---|---|---|"]
            for e in events:
                detail = audit_detail(e).replace("|", "/")
                lines.append(f"| {e['timestamp']} | {e['event']} | {e.get('tool', '')} | {detail} |")
        return "\n".join(lines).rstrip() + "\n"


def audit_detail(event: dict[str, Any]) -> str:
    """Resumen de una línea de un evento de auditoría."""
    kind = event.get("event")
    if kind == "confirmation":
        return "aprobada" if event.get("approved") else "rechazada"
    if kind == "tool_execution":
        return f"{'ok' if event.get('ok') else 'error'} en {event.get('duration_s', '?')} s"
    if kind == "tool_blocked":
        return str(event.get("reason", ""))[:120]
    if kind == "scope_added":
        return f"objetivo {event.get('target')}"
    return ""
