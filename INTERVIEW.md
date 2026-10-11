# Interview Notes

## Q1. Is LangGraph similar to Airflow?

Partly. They overlap on the idea of a graph of steps, but solve different problems.

**Similarities**
- Both model work as a graph of nodes (tasks or steps) connected by edges.
- Both handle ordering, branching, and retries.
- Both are defined in Python code.

**Differences**

| | Airflow | LangGraph |
|---|---|---|
| Purpose | Batch data pipelines and scheduling | LLM agents and stateful AI workflows |
| Graph shape | DAG (no cycles) | Cycles allowed, so an agent can loop: think, call a tool, think again |
| Trigger | Cron or schedule, run on a cadence | On demand, such as a user message |
| State | Tasks pass small values via XCom. Data usually lives externally. | A shared state object is passed through every node and checkpointed |
| Routing | Mostly static, decided at DAG definition | Dynamic, since the LLM or code picks the next node at runtime |
| Human in the loop | Not a core feature | Built in (pause, approve, resume) |
| Runtime | Long-running scheduler and workers | A library you call inside your app |

**Analogy:** Airflow is "run this ETL every night at 2am." LangGraph is "the user asked a question, so let the agent decide which tools to call, loop until it has an answer, and remember the conversation."

**In the ERP copilot:** LangGraph fits the agent side (routing a question to the SQLite MCP tools or Pinecone retrieval, looping if more info is needed). Airflow would only matter for scheduled jobs, such as nightly re-indexing of ERP docs into Pinecone.

---

## Q2. Difference between LangChain and LangGraph, and why do we need them?

**LangChain** is a toolkit of building blocks for LLM apps. **LangGraph** is an orchestration layer for controlling how those blocks run, especially in loops and branches. Both are from the same team, and LangGraph is built to work with LangChain.

**LangChain provides:**
- Model wrappers (OpenAI, Anthropic, etc.) behind one interface
- Prompt templates, output parsers
- Tool definitions, retrievers, vector store integrations (e.g. Pinecone)
- Simple chains: prompt -> model -> parser

**LangGraph provides:**
- A state object shared across steps
- Nodes (functions) and edges, including conditional edges and cycles
- Checkpointing (save and resume state, memory across turns)
- Human-in-the-loop pauses, streaming, and retries

**Why we need them**

You can call the Claude API directly without either. They help when your app grows past one call:

- **LangChain** removes glue code: switching models, wiring Pinecone retrieval, defining tools.
- **LangGraph** is for flows that aren't a straight line. An agent decides, calls a tool, inspects the result, and maybe calls another tool or retries. A hand-rolled `while` loop gets messy and hard to debug, pause, or resume. LangGraph makes the flow explicit and inspectable.

**ERP copilot example flow**
1. Classify the question: live order data (SQLite via MCP) or ERP knowledge docs (Pinecone)?
2. Call the right tool.
3. If the result is empty or ambiguous, loop back and retry or ask the user.
4. Generate the final answer.

Steps 1-3 are branching and looping (LangGraph). The Pinecone retriever and model wrappers are the LangChain parts.

**Caveat:** if the flow stays simple (one question, one tool call, one answer), plain API calls with tool use are enough, and both libraries add abstraction you may not need. Adopt LangGraph when you actually hit routing, loop, or memory needs.
