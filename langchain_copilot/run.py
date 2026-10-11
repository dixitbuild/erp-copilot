"""ERP Copilot with LangChain: same guard -> agent flow, but LangChain does the plumbing.

Run:  uv run --group lab python -m langchain_copilot.run "Which work orders are overdue?"
"""

import asyncio
import sys

from langchain.agents import create_agent

from erp_copilot.agents.guard import GUARD_PROMPT, GuardVerdict
from langchain_copilot.common import erp_system_prompt, get_llm, start_toolbox, to_langchain_tools

BLOCKED = "Please ask a relevant question about sales, purchase or work orders (or the message was blocked)."


async def check_query(llm, message: str) -> GuardVerdict:
    # replaces ~20 lines of manual JSON parsing in agents/guard.py
    guard = llm.with_structured_output(GuardVerdict, method="function_calling")
    try:
        return await guard.ainvoke(
            [("system", GUARD_PROMPT), ("user", f"<user_query>\n{message}\n</user_query>")]
        )
    except Exception:  # fail closed, like the original guard
        return GuardVerdict(category="other", is_relevant=False, injection_detected=False, reason="guard failed")


async def main(question: str) -> None:
    llm = get_llm()
    toolbox = await start_toolbox()
    try:
        verdict = await check_query(llm, question)
        print("guard:", verdict)
        if not verdict.allowed:
            print(BLOCKED)
            return
        # replaces llm.chat_with_tools (the hand-written tool loop)
        agent = create_agent(llm, to_langchain_tools(toolbox), system_prompt=erp_system_prompt())
        result = await agent.ainvoke({"messages": [("user", question)]})
        for message in result["messages"]:
            message.pretty_print()
    finally:
        await toolbox.stop()


if __name__ == "__main__":
    asyncio.run(main(" ".join(sys.argv[1:]) or "What is the total value of open sales orders?"))
