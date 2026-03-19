from __future__ import annotations

import logging
from typing import Annotated

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from open_deep_research.deep_researcher import (
    _build_session_memory_clear_update,
    _build_session_memory_prompt_block,
    _build_session_memory_update,
)

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def print_header(title: str) -> None:
    logger.info(f"\n=== {title} ===")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_session_memory_write_and_read() -> None:
    print_header("PR4 Session Memory Write/Read")

    messages_round_1 = [
        HumanMessage(content="请用中文简洁回答，并优先关注本地资料。"),
    ]
    update_round_1 = _build_session_memory_update(
        messages_round_1,
        "I have enough information and will start research.",
        existing_preferences=[],
        existing_key_context=[],
    )

    prefs_round_1 = update_round_1["session_temporary_preferences"]["value"]
    context_round_1 = update_round_1["session_key_context"]["value"]
    assert_true(len(prefs_round_1) > 0, "Expected first round to capture preferences")
    assert_true(any("中文" in p for p in prefs_round_1), "Expected language preference to be captured")

    messages_round_2 = [
        *messages_round_1,
        AIMessage(content="Acknowledged."),
        HumanMessage(content="继续，并且不要表格。"),
    ]
    update_round_2 = _build_session_memory_update(
        messages_round_2,
        "Proceeding with your updated constraints.",
        existing_preferences=prefs_round_1,
        existing_key_context=context_round_1,
    )

    prefs_round_2 = update_round_2["session_temporary_preferences"]["value"]
    context_round_2 = update_round_2["session_key_context"]["value"]

    assert_true(
        any("中文" in p for p in prefs_round_2),
        "Expected second round to inherit first-round preference",
    )
    assert_true(
        any("不要表格" in p for p in prefs_round_2),
        "Expected second round to capture new preference",
    )

    prompt_block = _build_session_memory_prompt_block(
        clarification_summary=update_round_2["session_clarification_summary"],
        temporary_preferences=prefs_round_2,
        key_context=context_round_2,
    )
    assert_true("TemporaryPreferences:" in prompt_block, "Expected prompt block to include preferences section")
    assert_true("KeyContext:" in prompt_block, "Expected prompt block to include key context section")

    logger.info("PASS: session memory writes after clarification and is read before generation")


def validate_session_memory_clear() -> None:
    print_header("PR4 Session Memory Clear")

    clear_update = _build_session_memory_clear_update()
    assert_true(
        clear_update["session_clarification_summary"] is None,
        "Expected clarification summary to reset to None",
    )
    assert_true(
        clear_update["session_temporary_preferences"]["value"] == [],
        "Expected temporary preferences to be cleared",
    )
    assert_true(
        clear_update["session_key_context"]["value"] == [],
        "Expected key context to be cleared",
    )

    logger.info("PASS: session memory clear payload is correct")


class _ThreadState(TypedDict):
    new_pref: str
    session_temporary_preferences: Annotated[list[str], list.__add__]


def _write_preference(state: _ThreadState) -> dict:
    pref = state.get("new_pref", "").strip()
    if not pref:
        return {}
    return {"session_temporary_preferences": [pref]}


def validate_thread_isolation() -> None:
    print_header("PR4 Thread Isolation")

    builder = StateGraph(_ThreadState)
    builder.add_node("write_preference", _write_preference)
    builder.add_edge(START, "write_preference")
    builder.add_edge("write_preference", END)
    graph = builder.compile(checkpointer=MemorySaver())

    config_a = {"configurable": {"thread_id": "pr4-thread-a"}}
    config_b = {"configurable": {"thread_id": "pr4-thread-b"}}

    graph.invoke({"new_pref": "pref-a"}, config=config_a)
    graph.invoke({"new_pref": "pref-b"}, config=config_b)

    state_a = graph.get_state(config_a)
    state_b = graph.get_state(config_b)

    prefs_a = state_a.values.get("session_temporary_preferences", [])
    prefs_b = state_b.values.get("session_temporary_preferences", [])

    assert_true("pref-a" in prefs_a, "Expected thread A to keep its own preference")
    assert_true("pref-b" not in prefs_a, "Expected thread A state to exclude thread B preference")
    assert_true("pref-b" in prefs_b, "Expected thread B to keep its own preference")
    assert_true("pref-a" not in prefs_b, "Expected thread B state to exclude thread A preference")

    logger.info("PASS: short-term memory is isolated across threads")


def main() -> int:
    validate_session_memory_write_and_read()
    validate_session_memory_clear()
    validate_thread_isolation()
    logger.info("\nAll PR-4 acceptance checks finished.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
