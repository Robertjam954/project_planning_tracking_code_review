"""CLI entrypoint for the control-room agent layer.

Usage:
    python -m agents "plan a new invoice app"
    python -m agents "which projects are stalled"
    python -m agents --help
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Make config safe to import before deps are installed
try:
    from agents.config import settings
    from agents.graph import get_graph
    from agents.memory import ConversationStore
except ImportError as e:
    print(f"Error: Failed to import agents. {e}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Control-room agent layer: ask for planning, tracking, reviewing, or history.",
        prog="python -m agents",
    )
    parser.add_argument("query", nargs="?", help="Natural language request for an agent")
    parser.add_argument("--session", help="Reuse an existing session ID (default: new)")
    parser.add_argument("--list-sessions", action="store_true", help="List past sessions")
    parser.add_argument("--history", help="Recall a specific session ID")
    parser.add_argument("--model", help="Override the default model")
    args = parser.parse_args()

    if args.list_sessions:
        store = ConversationStore()
        sessions = store.list_sessions()
        if sessions:
            print("Recent sessions:")
            for s in sessions:
                print(f"  {s['session_id']} | {s['title']} | {s['n_messages']} messages")
        else:
            print("No sessions yet.")
        store.close()
        return

    if args.history:
        store = ConversationStore()
        messages = store.get_messages(args.history)
        if messages:
            print(f"Session {args.history}:")
            for m in messages:
                print(f"  {m.role.upper()}: {m.content}")
        else:
            print(f"No messages in session {args.history}")
        store.close()
        return

    if not args.query:
        parser.print_help()
        return

    # Validate API key
    settings.require_api_key()

    # Override model if requested
    if args.model:
        settings.model = args.model

    # Set up session
    session_id = args.session
    store = ConversationStore()
    if not session_id:
        session_id = store.new_session(title=args.query[:80])
        print(f"Session {session_id}\n")
    else:
        store.ensure_session(session_id)

    store.add_message(session_id, "user", args.query)

    try:
        # Invoke the graph
        graph = get_graph()
        config = {
            "configurable": {"thread_id": session_id},
            "recursion_limit": settings.recursion_limit,
        }

        state = {
            "messages": [{"role": "user", "content": args.query}],
            "worker": "END",
            "context": "",
        }

        print("Thinking...\n")
        step_count = 0
        max_steps = settings.max_supervisor_steps

        # Stream events or invoke with a step limit
        try:
            for output in graph.stream(state, config):
                step_count += 1
                if step_count >= max_steps:
                    print(f"\n(Reached step limit; stopping.)")
                    break
        except Exception as e:
            print(f"Error during graph execution: {e}", file=sys.stderr)
            store.close()
            sys.exit(1)

        # Extract final response from messages
        if state.get("messages"):
            last_msg = state["messages"][-1]
            if isinstance(last_msg, dict):
                content = last_msg.get("content", "")
            else:
                content = getattr(last_msg, "content", "")

            # Handle both text and tool-use blocks
            if isinstance(content, str):
                print(content)
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        print(block.get("text", ""))

            # Save assistant response to memory
            if content:
                response_text = content if isinstance(content, str) else str(content)
                store.add_message(session_id, "assistant", response_text[:500])

    finally:
        store.close()


if __name__ == "__main__":
    main()
