from dui.agent.context import select_context


def turn(i: int, with_tool: bool = False) -> list[dict]:
    messages = [{"role": "user", "content": f"pregunta {i}"}]
    if with_tool:
        messages += [
            {"role": "assistant", "content": None, "tool_calls": [{"id": f"c{i}", "function": {}}]},
            {"role": "tool", "tool_call_id": f"c{i}", "content": "resultado"},
        ]
    messages.append({"role": "assistant", "content": f"respuesta {i}"})
    return messages


def test_short_history_is_untouched():
    history = turn(1) + turn(2)
    assert select_context(history) is history


def test_keeps_recent_messages_and_starts_on_user():
    history = [m for i in range(20) for m in turn(i, with_tool=True)]  # 80 mensajes
    selected = select_context(history, max_messages=10)
    assert len(selected) <= 10
    assert selected[0]["role"] == "user"
    assert selected[-1] == history[-1]


def test_never_starts_with_orphan_tool_result():
    history = [m for i in range(10) for m in turn(i, with_tool=True)]
    for limit in range(1, 30):
        selected = select_context(history, max_messages=limit)
        assert selected and selected[0]["role"] == "user"


def test_respects_character_budget():
    history = [{"role": "user", "content": "x" * 1000}, {"role": "assistant", "content": "y" * 1000}] * 10
    selected = select_context(history, max_messages=100, max_chars=3000)
    assert sum(len(m["content"]) for m in selected) <= 3000 and selected[0]["role"] == "user"


def test_single_huge_turn_is_kept_from_its_user_message():
    history = turn(1) + [
        {"role": "user", "content": "grande"},
        {"role": "assistant", "content": "z" * 10_000},
    ]
    selected = select_context(history, max_messages=60, max_chars=100)
    assert selected[0]["content"] == "grande"
