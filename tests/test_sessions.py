"""Pruebas del almacenamiento de sesiones en SQLite."""

from __future__ import annotations

import json

import pytest

from dui.security import AuditLog
from dui.storage import SessionNotFound, SessionStore, new_session_id

TURN = [
    {"role": "user", "content": "¿Qué puertos tiene abiertos mi router?"},
    {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {"id": "c1", "type": "function", "function": {"name": "port_scan", "arguments": '{"t": 1}'}}
        ],
    },
    {"role": "tool", "tool_call_id": "c1", "name": "port_scan", "content": "22/tcp abierto (ssh)"},
    {"role": "assistant", "content": "Tu router tiene el puerto **22** (SSH) abierto."},
]


@pytest.fixture
def store(tmp_path):
    s = SessionStore(tmp_path / "dui.db")
    yield s
    s.close()


def test_messages_roundtrip_including_tool_calls(store):
    store.create("s1", "gemini/x")
    store.append_messages("s1", TURN, model="gemini/x")
    assert store.load_messages("s1") == TURN
    session = store.get("s1")
    assert session.message_count == 4 and session.model == "gemini/x"
    assert session.title == "¿Qué puertos tiene abiertos mi router?"


def test_persists_across_connections(tmp_path):
    first = SessionStore(tmp_path / "dui.db")
    first.create("s1")
    first.append_messages("s1", TURN[:1])
    first.close()
    second = SessionStore(tmp_path / "dui.db")
    assert second.load_messages("s1") == TURN[:1]
    second.append_messages("s1", TURN[1:])
    assert [m["role"] for m in second.load_messages("s1")] == ["user", "assistant", "tool", "assistant"]
    second.close()


def test_title_is_truncated_and_kept(store):
    store.create("s1")
    store.append_messages("s1", [{"role": "user", "content": "palabra " * 30}])
    store.append_messages("s1", [{"role": "user", "content": "otra cosa"}])
    title = store.get("s1").title
    assert len(title) <= 60 and title.endswith("…")


def test_list_latest_and_empty_sessions(store):
    store.create("vacia")
    for sid in ("a", "b"):
        store.create(sid)
        store.append_messages(sid, TURN[:1])
    assert {s.id for s in store.list()} == {"a", "b"}  # las vacías no se listan
    assert store.latest().id in {"a", "b"}
    assert store.latest(exclude=store.latest().id).id in {"a", "b"}
    store.delete_empty()
    with pytest.raises(SessionNotFound):
        store.get("vacia")


def test_find_by_fragment(store):
    for sid in ("20261016_100000_aaa111", "20261016_110000_bbb222"):
        store.create(sid)
        store.append_messages(sid, TURN[:1])
    assert store.find("bbb222").id == "20261016_110000_bbb222"
    with pytest.raises(SessionNotFound, match="varias"):
        store.find("20261016")
    with pytest.raises(SessionNotFound):
        store.find("zzz")
    with pytest.raises(SessionNotFound):
        store.find("%")  # los comodines de LIKE se tratan como texto


def test_search_full_text_ignores_accents_and_case(store):
    store.create("s1")
    store.append_messages("s1", TURN)
    store.create("s2")
    store.append_messages("s2", [{"role": "user", "content": "whois de example.com"}])
    hits = store.search("router")
    assert [h.session.id for h in hits] == ["s1"] and "«router»" in hits[0].snippet
    assert [h.session.id for h in store.search("PUERTOS")] == ["s1"]
    assert [h.session.id for h in store.search("que")] == ["s1"]  # "¿Qué" sin acento
    assert [h.session.id for h in store.search("example.com")] == ["s2"]
    assert store.search('"; DROP TABLE') == [] and store.search("") == []


def test_delete_cascades_messages_audit_and_index(store):
    store.create("s1")
    store.append_messages("s1", TURN)
    store.record_audit("s1", "confirmation", {"tool": "port_scan", "approved": True}, "2026-10-16T10:00:00")
    store.delete("s1")
    assert store.load_messages("s1") == [] and store.audit_events("s1") == []
    assert store.search("router") == []


def test_audit_log_backed_by_store(store):
    audit = AuditLog("s1", store)
    audit.record("confirmation", tool="port_scan", arguments={"target": "192.168.1.1"}, approved=False)
    audit.record("tool_execution", tool="dns_lookup", ok=True, duration_s=0.1)
    assert audit.summary() == {
        "total_actions": 1,
        "approvals": 0,
        "rejections": 1,
        "tools_used": ["dns_lookup"],
    }
    assert store.audit_events("s1")[0]["arguments"] == {"target": "192.168.1.1"}
    audit.switch("s2")
    assert audit.events == []


def test_exports(store):
    store.create("s1", "gemini/x")
    store.append_messages("s1", TURN)
    store.record_audit("s1", "confirmation", {"tool": "port_scan", "approved": True}, "2026-10-16T10:00:00")
    md = store.export_markdown("s1")
    assert md.startswith("# ¿Qué puertos")
    assert "🔧 Herramienta `port_scan`" in md and "22/tcp abierto" in md and "| confirmation |" in md
    data = json.loads(store.export_json("s1"))
    assert data["session"]["id"] == "s1" and len(data["messages"]) == 4 and len(data["audit"]) == 1


def test_append_is_atomic(store):
    store.create("s1")
    with pytest.raises(TypeError):
        store.append_messages(
            "s1", [{"role": "user", "content": "ok"}, {"role": "user", "content": object()}]
        )
    assert store.load_messages("s1") == [] and store.get("s1").message_count == 0


def test_session_ids_are_unique_and_sortable():
    ids = [new_session_id() for _ in range(50)]
    assert len(set(ids)) == 50 and all(len(i) == 22 for i in ids)
