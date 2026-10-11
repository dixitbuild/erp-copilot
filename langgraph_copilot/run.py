"""Interactive chat over the LangGraph version. Memory works because every turn shares a thread_id.

Run:  uv run --group lab python -m langgraph_copilot.run            (chat, with memory)
      uv run --group lab python -m langgraph_copilot.run --diagram  (print the graph as Mermaid)
"""

import asyncio
import sys

from langchain_copilot.common import start_toolbox
from langgraph_copilot.graph import build_graph


async def main() -> None:
    toolbox = await start_toolbox()
    try:
        graph = build_graph(toolbox)
        if "--diagram" in sys.argv:
            print(graph.get_graph().draw_mermaid())
            return
        config = {"configurable": {"thread_id": "demo"}, "recursion_limit": 12}  # recursion_limit = max_steps
        print("ERP Copilot (LangGraph). Ctrl+C to quit.")
        while True:
            question = input("\nyou> ").strip()
            if not question:
                continue
            # stream_mode="updates" shows which node ran at each step
            async for update in graph.astream({"messages": [("user", question)]}, config, stream_mode="updates"):
                for node, data in update.items():
                    messages = data.get("messages") if data else None
                    last = messages[-1] if messages else None
                    detail = getattr(last, "tool_calls", None) or getattr(last, "content", "") if last else data
                    print(f"[{node}] {detail}")
    finally:
        await toolbox.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, EOFError):
        pass
