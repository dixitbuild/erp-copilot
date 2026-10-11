"""ERP Copilot as an explicit LangGraph: guard -> (refuse | agent <-> tools) -> END.

Each box in the diagram is a node, each arrow an edge, and the agent <-> tools arrow is a cycle.
"""

from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from erp_copilot.agents.guard import GUARD_PROMPT, GuardVerdict
from langchain_copilot.common import erp_system_prompt, get_llm, to_langchain_tools

INJECTION_MESSAGE = "Your message looks like an attempt to manipulate the assistant, so it was blocked."
IRRELEVANT_MESSAGE = "Please ask a relevant question about sales orders, purchase orders or work orders."


class State(TypedDict):
    messages: Annotated[list, add_messages]  # reducer appends instead of overwriting
    verdict: dict | None  # GuardVerdict.model_dump(); plain dict keeps the checkpoint serializable


def build_graph(toolbox):
    llm = get_llm()
    tools = to_langchain_tools(toolbox)
    llm_with_tools = llm.bind_tools(tools)
    guard_llm = llm.with_structured_output(GuardVerdict, method="function_calling")
    system = SystemMessage(erp_system_prompt())

    async def guard(state: State) -> dict:
        # the guard is stateless, so show it the recent user turns or follow-ups look "irrelevant"
        recent = [m.content for m in state["messages"] if m.type == "human"][-3:]
        question = "\n".join(recent)
        try:
            verdict = await guard_llm.ainvoke(
                [("system", GUARD_PROMPT), ("user", f"<user_query>\n{question}\n</user_query>")]
            )
        except Exception:  # fail closed
            verdict = GuardVerdict(category="other", is_relevant=False, injection_detected=False)
        return {"verdict": verdict.model_dump()}

    async def refuse(state: State) -> dict:
        text = INJECTION_MESSAGE if state["verdict"]["injection_detected"] else IRRELEVANT_MESSAGE
        return {"messages": [AIMessage(text)]}

    async def agent(state: State) -> dict:
        return {"messages": [await llm_with_tools.ainvoke([system, *state["messages"]])]}

    def route_after_guard(state: State) -> str:  # conditional edge
        return "agent" if GuardVerdict(**state["verdict"]).allowed else "refuse"

    g = StateGraph(State)
    g.add_node("guard", guard)
    g.add_node("refuse", refuse)
    g.add_node("agent", agent)
    g.add_node("tools", ToolNode(tools, handle_tool_errors=True))
    g.add_edge(START, "guard")
    g.add_conditional_edges("guard", route_after_guard, ["agent", "refuse"])
    g.add_conditional_edges("agent", tools_condition)  # tool call -> "tools", else END
    g.add_edge("tools", "agent")  # the cycle
    g.add_edge("refuse", END)
    return g.compile(checkpointer=InMemorySaver())  # checkpointer = per-thread conversation memory
